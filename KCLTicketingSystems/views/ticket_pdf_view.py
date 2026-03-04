import io
from datetime import timezone as dt_timezone

from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from ..models import Ticket


# ---------------------------------------------------------------------------
# Colour palette
# ---------------------------------------------------------------------------
KCL_RED = colors.HexColor("#990000")
STUDENT_BG = colors.HexColor("#E8F4FD")
STAFF_BG = colors.HexColor("#F0F7EE")
BORDER_GREY = colors.HexColor("#CCCCCC")
LABEL_GREY = colors.HexColor("#555555")


def _build_styles():
    """Return a dict of named ParagraphStyles used in the PDF."""
    base = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "KCLTitle",
        parent=base["Title"],
        fontSize=20,
        textColor=KCL_RED,
        spaceAfter=2 * mm,
    )
    subtitle_style = ParagraphStyle(
        "KCLSubtitle",
        parent=base["Normal"],
        fontSize=10,
        textColor=LABEL_GREY,
        spaceAfter=6 * mm,
    )
    section_heading_style = ParagraphStyle(
        "SectionHeading",
        parent=base["Heading2"],
        fontSize=12,
        textColor=KCL_RED,
        spaceBefore=4 * mm,
        spaceAfter=2 * mm,
    )
    label_style = ParagraphStyle(
        "Label",
        parent=base["Normal"],
        fontSize=9,
        textColor=LABEL_GREY,
        leading=14,
    )
    value_style = ParagraphStyle(
        "Value",
        parent=base["Normal"],
        fontSize=10,
        leading=14,
    )
    sender_student_style = ParagraphStyle(
        "SenderStudent",
        parent=base["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#1A6FAF"),
        spaceAfter=1 * mm,
        fontName="Helvetica-Bold",
    )
    sender_staff_style = ParagraphStyle(
        "SenderStaff",
        parent=base["Normal"],
        fontSize=9,
        textColor=colors.HexColor("#2E7D32"),
        spaceAfter=1 * mm,
        fontName="Helvetica-Bold",
    )
    message_style = ParagraphStyle(
        "Message",
        parent=base["Normal"],
        fontSize=10,
        leading=15,
    )
    timestamp_style = ParagraphStyle(
        "Timestamp",
        parent=base["Normal"],
        fontSize=8,
        textColor=LABEL_GREY,
        spaceBefore=1 * mm,
    )

    return {
        "title": title_style,
        "subtitle": subtitle_style,
        "section_heading": section_heading_style,
        "label": label_style,
        "value": value_style,
        "sender_student": sender_student_style,
        "sender_staff": sender_staff_style,
        "message": message_style,
        "timestamp": timestamp_style,
    }


def _format_datetime(dt):
    """Return a human-readable datetime string, handling both aware and naive."""
    if dt is None:
        return "Unknown"
    if dt.tzinfo is not None:
        dt = dt.astimezone(dt_timezone.utc).replace(tzinfo=None)
    return dt.strftime("%d %B %Y at %H:%M UTC")


def _build_pdf(ticket) -> bytes:
    """Construct the PDF in memory and return the raw bytes."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        title=f"Ticket #{ticket.id} Summary",
        author="KCL Ticketing System",
    )

    styles = _build_styles()
    story = []

    # ------------------------------------------------------------------
    # Header
    # ------------------------------------------------------------------
    story.append(Paragraph("KCL Ticketing System", styles["title"]))
    story.append(
        Paragraph(
            f"Ticket #{ticket.id} — Conversation Summary &nbsp;&nbsp;|&nbsp;&nbsp; "
            f"Generated: {_format_datetime(__import__('django.utils.timezone', fromlist=['now']).timezone.now())}",
            styles["subtitle"],
        )
    )
    story.append(HRFlowable(width="100%", thickness=1.5, color=KCL_RED, spaceAfter=4 * mm))

    # ------------------------------------------------------------------
    # Ticket metadata table
    # ------------------------------------------------------------------
    story.append(Paragraph("Ticket Details", styles["section_heading"]))

    student_name = (
        f"{ticket.user.first_name} {ticket.user.last_name}".strip()
        if ticket.user
        else f"{ticket.name} {ticket.surname}".strip() or "Unknown"
    )
    assigned_name = (
        f"{ticket.assigned_to.first_name} {ticket.assigned_to.last_name}".strip()
        if ticket.assigned_to
        else "Unassigned"
    )

    meta_rows = [
        [Paragraph("Student", styles["label"]),    Paragraph(student_name, styles["value"])],
        [Paragraph("Department", styles["label"]), Paragraph(ticket.department, styles["value"])],
        [Paragraph("Issue Type", styles["label"]), Paragraph(ticket.type_of_issue, styles["value"])],
        [Paragraph("Status", styles["label"]),     Paragraph(ticket.status.replace("_", " ").title(), styles["value"])],
        [Paragraph("Priority", styles["label"]),   Paragraph(ticket.priority.title(), styles["value"])],
        [Paragraph("Assigned To", styles["label"]), Paragraph(assigned_name, styles["value"])],
        [Paragraph("Opened", styles["label"]),     Paragraph(_format_datetime(ticket.created_at), styles["value"])],
    ]

    meta_table = Table(meta_rows, colWidths=[40 * mm, None])
    meta_table.setStyle(TableStyle([
        ("VALIGN",       (0, 0), (-1, -1), "TOP"),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.white, colors.HexColor("#F9F9F9")]),
        ("GRID",         (0, 0), (-1, -1), 0.5, BORDER_GREY),
        ("LEFTPADDING",  (0, 0), (-1, -1), 3 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
        ("TOPPADDING",   (0, 0), (-1, -1), 2 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2 * mm),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 4 * mm))

    # Original message from student
    story.append(Paragraph("Original Message", styles["section_heading"]))
    story.append(Paragraph(ticket.additional_details or "(no message)", styles["message"]))
    story.append(Spacer(1, 4 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_GREY, spaceAfter=4 * mm))

    # ------------------------------------------------------------------
    # Conversation thread
    # ------------------------------------------------------------------
    story.append(Paragraph("Conversation Thread", styles["section_heading"]))

    replies = ticket.replies.select_related("user").order_by("created_at")

    if not replies.exists():
        story.append(Paragraph("No replies yet.", styles["message"]))
    else:
        for reply in replies:
            role = getattr(reply.user, "role", "student") if reply.user else "student"
            is_staff = role in ("staff", "Staff", "admin", "Admin")

            full_name = (
                f"{reply.user.first_name} {reply.user.last_name}".strip()
                if reply.user
                else "Unknown User"
            )
            role_label = "Staff" if is_staff else "Student"
            sender_style = styles["sender_staff"] if is_staff else styles["sender_student"]

            # Build a mini-table per message to create a coloured card effect
            inner_content = [
                [Paragraph(f"{full_name} &nbsp;({role_label})", sender_style)],
                [Paragraph(reply.body, styles["message"])],
                [Paragraph(_format_datetime(reply.created_at), styles["timestamp"])],
            ]
            inner_table = Table(inner_content, colWidths=["100%"])
            bg = STAFF_BG if is_staff else STUDENT_BG
            inner_table.setStyle(TableStyle([
                ("BACKGROUND",   (0, 0), (-1, -1), bg),
                ("BOX",          (0, 0), (-1, -1), 0.75, BORDER_GREY),
                ("LEFTPADDING",  (0, 0), (-1, -1), 3 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
                ("TOPPADDING",   (0, 0), (-1, -1), 2 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2 * mm),
                ("VALIGN",       (0, 0), (-1, -1), "TOP"),
            ]))
            story.append(inner_table)
            story.append(Spacer(1, 3 * mm))

    # ------------------------------------------------------------------
    # Footer note
    # ------------------------------------------------------------------
    story.append(Spacer(1, 6 * mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=BORDER_GREY, spaceAfter=2 * mm))
    story.append(
        Paragraph(
            "This document is an official record generated by the KCL Ticketing System. "
            "Do not alter its contents.",
            ParagraphStyle(
                "Footer",
                parent=getSampleStyleSheet()["Normal"],
                fontSize=8,
                textColor=LABEL_GREY,
            ),
        )
    )

    doc.build(story)
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# View
# ---------------------------------------------------------------------------

@api_view(["GET"])
@permission_classes([IsAuthenticated])
def ticket_pdf(request, ticket_id):
    """
    Return a PDF summary of a ticket's conversation.

    Only the student who owns the ticket may download it.
    Staff/admin access is deliberately restricted here — they have their
    own dashboard views. Adjust the permission check below if that changes.
    """
    ticket = get_object_or_404(Ticket, pk=ticket_id)

    # Ownership check — student must own this ticket
    if ticket.user != request.user:
        return Response(
            {"detail": "You do not have permission to download this ticket's summary."},
            status=status.HTTP_403_FORBIDDEN,
        )

    pdf_bytes = _build_pdf(ticket)

    response = HttpResponse(pdf_bytes, content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="ticket_{ticket.id}_summary.pdf"'
    )
    return response
