# PackItUp System Workflow Diagrams

---

## 1. Ticket Creation Workflow

### Diagram

```mermaid
flowchart TD
    A(["Student opens Create Ticket form"]) --> B["Selects Department & Issue Type"]
    B --> C["Writes description, attaches files"]
    C --> D["Submits ticket"]
    D --> E["System auto-assigns ticket to\nstaff member with fewest open tickets\nin that department"]
    E --> F["All admins receive a notification:\n'New Ticket Submitted'"]
    F --> G["Ticket appears on Student's\nDashboard as 'Pending'"]

    G --> H["Staff/Admin views ticket\nand replies"]
    H --> I["Student receives notification:\n'New Reply on Your Ticket'"]
    I --> J["Ticket status changes to\n'Awaiting Response'"]

    J --> K{"Student responds?"}
    K -->|Yes| L["Student replies"]
    L --> M["Ticket status changes to\n'In Progress'"]
    M --> N["Staff receives notification:\n'Student replied'"]
    N --> H

    K -->|No reply for 3 days| O["System auto-closes ticket"]

    H --> P{"Issue resolved?"}
    P -->|Yes| Q["Student or Staff closes the ticket"]
    Q --> R["Ticket status changes to 'Closed'\nBoth parties notified"]
    R --> S["Student can download a\nPDF summary of the ticket\n(includes full conversation thread)"]
    S --> T(["Workflow Complete"])

    style A fill:#e1f5fe,color:#000
    style T fill:#c8e6c9,color:#000
    style O fill:#fff9c4,color:#000
    style S fill:#e8f5e9,color:#000
```

### Description

> A **student** creates a ticket by selecting a department, issue type, writing a description (with optional file attachments and priority). Upon submission, the system **automatically assigns** the ticket to the least-busy staff member in that department, and **all admins are notified**. The assigned staff member reviews and replies, which **notifies the student** and sets the ticket to "Awaiting Response". The student and staff exchange replies in a back-and-forth conversation, with the ticket toggling between "In Progress" and "Awaiting Response". If the student does not reply within **3 days**, the system **auto-closes** the ticket. Once the issue is resolved, either party can **close the ticket**, and the student can then **download a PDF summary** containing the full ticket details and conversation history.

---

## 2. Meeting Request Workflow

### Diagram

```mermaid
flowchart TD
    A(["Student browses Staff Directory"]) --> B["Searches by name or\nfilters by department"]
    B --> C["Clicks 'Book Meeting'\non a staff member"]
    C --> D["Views staff member's profile\nand office hours"]
    D --> E["Selects a date"]
    E --> F["System shows available\n15-minute time slots"]
    F --> G["Student picks a slot\nand writes a reason"]
    G --> H["Submits meeting request"]

    H --> I["Staff member receives notification:\n'New Meeting Request'"]
    I --> J["Request appears as 'Pending'\non Staff's Meeting Dashboard"]

    J --> K{"Staff decision"}

    K -->|Accept| L["Status changes to 'Accepted'"]
    L --> M["Student receives notification:\n'Meeting request accepted'"]
    M --> N["Meeting appears on Staff's\nWeekly Calendar"]
    N --> O(["Meeting takes place"])

    K -->|Deny| P["Status changes to 'Denied'"]
    P --> Q["Student receives notification:\n'Meeting request denied'"]
    Q --> R["Time slot becomes available\nagain for other students"]

    style A fill:#e1f5fe,color:#000
    style O fill:#c8e6c9,color:#000
    style L fill:#c8e6c9,color:#000
    style P fill:#ffcdd2,color:#000
```

### Description

> A **student** browses the Staff Directory (searchable by name, filterable by department), selects a staff member, and views their profile and office hours. After choosing a date, the system displays **available 15-minute time slots** (calculated from office hours minus already-booked meetings). The student selects a slot, provides a reason, and submits the request. The **staff member is notified** and sees the request as "Pending" on their Meeting Dashboard. The staff member can **accept** (the meeting appears on their Weekly Calendar and the student is notified) or **deny** (the student is notified and the time slot becomes available again for others).

---

## 3. Office Hours Management Workflow

### Diagram

```mermaid
flowchart TD
    A(["Staff opens Meeting\nRequests Dashboard"]) --> B["Views current office hours\nand weekly calendar"]

    B --> C{"Action?"}

    C -->|Add availability| D["Selects day of the week,\nstart time, and end time"]
    D --> E["Clicks 'Add Block'"]
    E --> F["New office hours block\nappears in the list"]
    F --> G["Students can now book\n15-min slots during\nthose hours"]
    G --> C

    C -->|Remove availability| H["Clicks delete on an\nexisting office hours block"]
    H --> I["Confirms deletion"]
    I --> J["Block removed from list"]
    J --> K["No new bookings allowed\nfor that time range"]
    K --> L["Note: Already-accepted\nmeetings are NOT cancelled"]
    L --> C

    C -->|View calendar| M["Weekly Calendar shows:\n- Office hours as light blocks\n- Accepted meetings as dark blocks"]
    M --> N["Hover over a meeting to see\nstudent name, email, and reason"]

    style A fill:#fff3e0,color:#000
    style G fill:#c8e6c9,color:#000
    style L fill:#fff9c4,color:#000
```

### Description

> A **staff member** manages their availability from the Meeting Requests Dashboard. They can **add office hours** by selecting a day, start time, and end time — once saved, students can book 15-minute slots during those hours. They can **remove office hours** blocks (with a confirmation prompt), which prevents new bookings for that time range but does **not cancel** already-accepted meetings. The **Weekly Calendar** provides a visual overview: office hours appear as light blocks and accepted meetings as darker blocks, with hover tooltips showing student details.

---

## 4. Ticket Reporting Workflow

### Diagram

```mermaid
flowchart TD
    A(["Admin opens Dashboard"]) --> B["Views summary cards:\nTotal / Pending / In Progress /\nResolved / Closed tickets"]
    B --> C["Views recent tickets table\n(last 7 days)"]

    C --> D["Navigates to Statistics page"]

    D --> E["Selects date range:\nLast 7 / 30 / 90 days\nor custom dates"]

    E --> F["System calculates per-department:\n- Ticket counts by status\n- Ticket counts by priority\n- Avg resolution time\n- Avg response time"]

    F --> G{"View mode?"}

    G -->|Table View| H["Department breakdown table\nwith status counts, priority\ncounts, and average times"]

    G -->|Graph View| I["Bar charts showing:\n- Status distribution\n- Tickets by department\n- Priority distribution"]

    H & I --> J{"Export?"}
    J -->|Export Statistics CSV| K["Downloads per-department\nsummary as CSV"]
    J -->|Export All Tickets CSV| L["Downloads individual\nticket records as CSV"]
    J -->|No export needed| M(["Done"])

    style A fill:#f3e5f5,color:#000
    style M fill:#c8e6c9,color:#000
    style K fill:#e8f5e9,color:#000
    style L fill:#e8f5e9,color:#000
```

### Description

> An **admin** views the Dashboard which shows summary cards (total, pending, in-progress, resolved, closed ticket counts) and a recent tickets table. On the **Statistics page**, the admin selects a date range (quick presets or custom dates), and the system calculates **per-department analytics**: ticket counts by status and priority, average resolution time, and average response time to first staff reply. Results can be viewed as **tables** or **bar charts**. The admin can **export** the data as CSV — either a per-department summary or a full list of individual ticket records.

---

## Rendering Instructions

These diagrams use **Mermaid** syntax. To render them:
- **VS Code**: Install the "Markdown Preview Mermaid Support" extension
- **GitHub**: Mermaid diagrams render natively in `.md` files
- **Online**: Paste the mermaid code blocks at [mermaid.live](https://mermaid.live)
- **Export to PNG/SVG**: Use the Mermaid CLI (`mmdc`) or mermaid.live export feature
