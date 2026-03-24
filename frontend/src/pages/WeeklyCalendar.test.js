import React from "react";
import { render, screen, fireEvent } from "@testing-library/react";
import "@testing-library/jest-dom";
import WeeklyCalendar from "./WeeklyCalendar";

describe("WeeklyCalendar", () => {
  const officeHours = [
    { id: 1, day_of_week: "Monday", start_time: "09:00:00", end_time: "11:00:00" },
    { id: 2, day_of_week: "Wednesday", start_time: "13:00:00", end_time: "15:00:00" },
  ];

  const meetings = [
    {
      id: 1,
      student_name: "John Doe",
      student_email: "john@kcl.ac.uk",
      meeting_datetime: "2026-03-23T09:15:00Z",
      description: "Need guidance",
      status: "accepted",
    },
  ];

  test("renders navigation, legend and weekday headers", () => {
    render(<WeeklyCalendar officeHours={officeHours} acceptedMeetings={meetings} />);

    expect(screen.getByRole("button", { name: /prev/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /next/i })).toBeInTheDocument();
    expect(screen.getByText(/office hours/i)).toBeInTheDocument();
    expect(screen.getByText(/accepted meeting/i)).toBeInTheDocument();
    expect(screen.getByText("Mon")).toBeInTheDocument();
  });

  test("moves week backward and forward", () => {
    render(<WeeklyCalendar officeHours={officeHours} acceptedMeetings={meetings} />);

    const labelBefore = screen.getByText(/–/i).textContent;
    fireEvent.click(screen.getByRole("button", { name: /next/i }));
    const labelAfterNext = screen.getByText(/–/i).textContent;
    expect(labelAfterNext).not.toEqual(labelBefore);

    fireEvent.click(screen.getByRole("button", { name: /prev/i }));
    const labelAfterPrev = screen.getByText(/–/i).textContent;
    expect(labelAfterPrev).toEqual(labelBefore);
  });

  test("shows and hides tooltip on meeting hover", () => {
    render(<WeeklyCalendar officeHours={officeHours} acceptedMeetings={meetings} />);

    const meetingBlock = screen.getByText("John");
    meetingBlock.getBoundingClientRect = () => ({ right: 100, left: 50, top: 50 });

    fireEvent.mouseEnter(meetingBlock);
    expect(screen.getByText(/john@kcl.ac.uk/i)).toBeInTheDocument();
    expect(screen.getByText(/need guidance/i)).toBeInTheDocument();

    fireEvent.mouseLeave(meetingBlock);
    expect(screen.queryByText(/john@kcl.ac.uk/i)).not.toBeInTheDocument();
  });

  test("renders safely with empty props and default hours", () => {
    render(<WeeklyCalendar officeHours={[]} acceptedMeetings={[]} />);
    expect(screen.getByText(/08:00/i)).toBeInTheDocument();
    expect(screen.getByText(/17:00/i)).toBeInTheDocument();
  });
});
