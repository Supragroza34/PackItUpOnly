import { useState } from "react";

const DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];
const HOUR_HEIGHT = 56; // px per hour
const HEADER_H   = 36; // px for the day-name header row


function getMondayOfWeek(date) {
  const d = new Date(date);
  const day = d.getDay();                
  const diff = day === 0 ? -6 : 1 - day; 
  d.setDate(d.getDate() + diff);
  d.setHours(0, 0, 0, 0);
  return d;
}

function addDays(date, n) {
  const d = new Date(date);
  d.setDate(d.getDate() + n);
  return d;
}

function parseTimeToMinutes(timeStr) {
  const [h, m] = timeStr.split(":").map(Number);
  return h * 60 + (m || 0);
}

function formatWeekLabel(start) {
  const end = addDays(start, 6);
  const fmt = (d) => d.toLocaleDateString("en-GB", { day: "numeric", month: "short" });
  return `${fmt(start)} – ${fmt(end)} ${end.getFullYear()}`;
}

const TOOLTIP_WIDTH = 240;

export default function WeeklyCalendar({ officeHours, acceptedMeetings }) {
  const [weekStart, setWeekStart] = useState(() => getMondayOfWeek(new Date()));
  const [tooltip, setTooltip] = useState(null); 

  function showTooltip(e, m) {
    const rect = e.currentTarget.getBoundingClientRect();
    let x = rect.right + 10;
    if (x + TOOLTIP_WIDTH > window.innerWidth - 8) {
      x = rect.left - TOOLTIP_WIDTH - 10;
    }
    const y = Math.min(rect.top, window.innerHeight - 180);
    setTooltip({ meeting: m, x, y });
  }

  function hideTooltip() {
    setTooltip(null);
  }
  const days = Array.from({ length: 7 }, (_, i) => addDays(weekStart, i));

  let minMin = 8 * 60;
  let maxMin = 18 * 60;
  officeHours.forEach((oh) => {
    minMin = Math.min(minMin, parseTimeToMinutes(oh.start_time));
    maxMin = Math.max(maxMin, parseTimeToMinutes(oh.end_time));
  });
  minMin = Math.floor(minMin / 60) * 60;
  maxMin = Math.ceil(maxMin  / 60) * 60;

  const totalMin  = maxMin - minMin;
  const hourCount = totalMin / 60;
  const calH      = hourCount * HOUR_HEIGHT;

  function toTop(minutes) {
    return ((minutes - minMin) / 60) * HOUR_HEIGHT;
  }

  function isSameDay(isoStr, day) {
    const d = new Date(isoStr);
    return (
      d.getUTCFullYear() === day.getFullYear() &&
      d.getUTCMonth()    === day.getMonth()    &&
      d.getUTCDate()     === day.getDate()
    );
  }

  return (
    <div className="wc-root">

      {/* ── Week navigation ── */}
      <div className="wc-nav">
        <button className="wc-nav-btn" onClick={() => setWeekStart((d) => addDays(d, -7))}>
          ‹ Prev
        </button>
        <span className="wc-week-label">{formatWeekLabel(weekStart)}</span>
        <button className="wc-nav-btn" onClick={() => setWeekStart((d) => addDays(d, 7))}>
          Next ›
        </button>
      </div>

      {/* ── Scrollable calendar body ── */}
      <div className="wc-scroll">
        <div className="wc-inner">

          {/* Time gutter */}
          <div className="wc-gutter">
            <div className="wc-gutter-spacer" style={{ height: HEADER_H }} />
            <div className="wc-gutter-body" style={{ height: calH }}>
              {Array.from({ length: hourCount }, (_, i) => (
                <div
                  key={i}
                  className="wc-hour-label"
                  style={{ top: i * HOUR_HEIGHT }}
                >
                  {String(Math.floor(minMin / 60) + i).padStart(2, "0")}:00
                </div>
              ))}
            </div>
          </div>

          {/* Day columns */}
          <div className="wc-days">
            {days.map((day, i) => {
              const name       = DAY_NAMES[i];
              const dayOH      = officeHours.filter((oh) => oh.day_of_week === name);
              const dayMtg     = acceptedMeetings.filter((m) => isSameDay(m.meeting_datetime, day));
              const isToday    = day.toDateString() === new Date().toDateString();

              return (
                <div key={i} className="wc-day-col">

                  {/* Day header */}
                  <div
                    className={`wc-day-hdr${isToday ? " wc-day-hdr-today" : ""}`}
                    style={{ height: HEADER_H }}
                  >
                    <span className="wc-day-name">{name.slice(0, 3)}</span>
                    <span className="wc-day-date">{day.getDate()}</span>
                  </div>

                  {/* Events area */}
                  <div className="wc-day-body" style={{ height: calH }}>

                    {/* Horizontal hour lines */}
                    {Array.from({ length: hourCount }, (_, j) => (
                      <div
                        key={j}
                        className="wc-gridline"
                        style={{ top: j * HOUR_HEIGHT }}
                      />
                    ))}

                    {/* Office-hours availability blocks */}
                    {dayOH.map((oh, k) => {
                      const top = toTop(parseTimeToMinutes(oh.start_time));
                      const h   = toTop(parseTimeToMinutes(oh.end_time)) - top;
                      return (
                        <div
                          key={k}
                          className="wc-oh-block"
                          style={{ top, height: h }}
                        />
                      );
                    })}

                    {/* Accepted-meeting blocks (15-min slots) */}
                    {dayMtg.map((m, k) => {
                      const d      = new Date(m.meeting_datetime);
                      const startM = d.getUTCHours() * 60 + d.getUTCMinutes();
                      const top    = toTop(startM);
                      const h      = Math.max((15 / 60) * HOUR_HEIGHT, 18);
                      return (
                        <div
                          key={k}
                          className="wc-mtg-block"
                          style={{ top, height: h }}
                          onMouseEnter={(e) => showTooltip(e, m)}
                          onMouseLeave={hideTooltip}
                        >
                          {m.student_name?.split(" ")[0]}
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {/* ── Hover tooltip ── */}
      {tooltip && (
        <div
          className="wc-tooltip"
          style={{ left: tooltip.x, top: tooltip.y }}
        >
          <div className="wc-tooltip-name">{tooltip.meeting.student_name}</div>
          <div className="wc-tooltip-email">{tooltip.meeting.student_email}</div>
          <div className="wc-tooltip-time">
            {new Date(tooltip.meeting.meeting_datetime).toLocaleString("en-GB", {
              weekday: "short", day: "numeric", month: "short",
              hour: "2-digit", minute: "2-digit",
              timeZone: "UTC",
            })}
          </div>
          {tooltip.meeting.description && (
            <div className="wc-tooltip-desc">{tooltip.meeting.description}</div>
          )}
        </div>
      )}

      {/* ── Legend ── */}
      <div className="wc-legend">
        <span className="wc-legend-oh">Office Hours</span>
        <span className="wc-legend-mtg">Accepted Meeting</span>
      </div>
    </div>
  );
}
