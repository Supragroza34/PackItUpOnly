import { useEffect, useState } from "react";

function StaffMeetingRequestsPage() {
  const [meeting_requests, setMeetingRequests] = useState([]);

  useEffect(() => {
    fetch("/api/staff/dashboard/meeting-requests/")
      .then(res => res.json())
      .then(data => setMeetingRequests(data));
  }, []);

  return (
    <div>
      <h1>Meeting Requests</h1>

      <ul>
        {meeting_requests.map(meeting_request => (
          <li key={meeting_request.id}>
            <strong>{meeting_request.user.name}</strong>: {meeting_request.description}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default StaffMeetingRequestsPage;