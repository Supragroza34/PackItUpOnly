export const FAQ_CATEGORIES = [
  'All',
  'Tickets',
  'Account',
  'Tracking',
  'Students',
  'Staff',
  'General'
];

export const faqItems = [
  {
    id: 'ticket-create-basics',
    question: 'How do I create a new ticket?',
    answer:
      'Open the Create Ticket page and complete the required fields before submitting.\n\n- Enter your name and surname\n- Add your K-Number to auto-fill your KCL email\n- Choose your department and issue type\n- Add enough detail so support can reproduce the problem',
    category: 'Tickets',
    audience: 'all',
    tags: ['create', 'submit', 'new ticket', 'form']
  },
  {
    id: 'ticket-auto-filled-fields',
    question: 'Which details are filled in automatically when I create a ticket?',
    answer:
      'When you enter your K-Number, the platform auto-generates your KCL email.\n\nDate and time are also recorded automatically when the ticket is created so activity can be tracked accurately.',
    category: 'Tickets',
    audience: 'all',
    tags: ['auto fill', 'k-number', 'email', 'timestamp']
  },
  {
    id: 'ticket-department-category',
    question: 'How should I choose the right department and issue category?',
    answer:
      'Start with the department that owns the system or process you are reporting.\n\nIf two categories seem valid, pick the closest one and explain context in Additional Details so your request can still be routed correctly.',
    category: 'Tickets',
    audience: 'all',
    tags: ['department', 'category', 'routing']
  },
  {
    id: 'tracking-status-meaning',
    question: 'What do ticket statuses mean?',
    answer:
      '- Open: your ticket is submitted and waiting for action\n- In Progress: a staff member is actively working on it\n- Waiting on You: support needs more information from you\n- Resolved/Closed: work is complete and ticket is finished',
    category: 'Tracking',
    audience: 'all',
    tags: ['status', 'open', 'in progress', 'closed']
  },
  {
    id: 'tracking-check-updates',
    question: 'How can I track updates on my ticket?',
    answer:
      'Use the ticket tracking area from your dashboard to view the latest status and responses.\n\nCheck the most recent staff comment first, then reply directly on the same ticket if clarification is requested.',
    category: 'Tracking',
    audience: 'all',
    tags: ['track', 'updates', 'dashboard', 'responses']
  },
  {
    id: 'ticket-edit-or-add-details',
    question: 'Can I update my ticket after submission?',
    answer:
      'Yes. Open the ticket and add a follow-up response with any new details, screenshots, or timeline changes.\n\nKeeping all updates on the same ticket helps support avoid duplicate work.',
    category: 'Tickets',
    audience: 'all',
    tags: ['edit', 'update', 'add details', 'follow-up']
  },
  {
    id: 'students-respond-staff',
    question: 'I am a student. How do I reply when staff asks for more information?',
    answer:
      'Open your ticket and respond in the reply section with precise steps, error text, and when the issue started.\n\n- Include what you already tried\n- Attach relevant screenshots\n- Confirm whether the issue is still happening',
    category: 'Students',
    audience: 'student',
    tags: ['student', 'reply', 'more information']
  },
  {
    id: 'students-missing-ticket',
    question: 'I am a student and cannot find my ticket. What should I do?',
    answer:
      'First, search by keywords or date in your ticket list.\n\nIf it still does not appear, create a new ticket with a note that a prior submission may have failed so support can cross-check.',
    category: 'Students',
    audience: 'student',
    tags: ['student', 'missing', 'not visible', 'ticket list']
  },
  {
    id: 'staff-assigned-tickets',
    question: 'How do staff members view tickets assigned to them?',
    answer:
      'Use the staff queue or assigned view in the portal to see tickets routed to you.\n\nSort by priority or newest activity to triage quickly during busy periods.',
    category: 'Staff',
    audience: 'staff',
    tags: ['staff', 'assigned', 'queue', 'triage']
  },
  {
    id: 'staff-reply-close-ticket',
    question: 'How should staff respond and close a ticket?',
    answer:
      'Post a clear response that includes the resolution steps and any follow-up the requester must complete.\n\nClose the ticket only after confirming the issue is resolved or after a documented inactivity window.',
    category: 'Staff',
    audience: 'staff',
    tags: ['staff', 'respond', 'close ticket', 'resolution']
  },
  {
    id: 'account-password-reset',
    question: 'How do I reset my password?',
    answer:
      'Use the account recovery or password reset option on the login page.\n\nIf you do not receive a reset email, check spam and then submit a ticket under Account support.',
    category: 'Account',
    audience: 'all',
    tags: ['password', 'reset', 'login']
  },
  {
    id: 'account-profile-changes',
    question: 'Can I change my account details after registration?',
    answer:
      'Basic profile details can usually be updated from your account settings.\n\nFor identity-related fields tied to university records, raise an Account ticket so staff can verify and update securely.',
    category: 'Account',
    audience: 'all',
    tags: ['account', 'profile', 'update details']
  },
  {
    id: 'general-attachments',
    question: 'What should I include in Additional Details for faster support?',
    answer:
      '- Exact error message text\n- Device or browser used\n- Time the issue occurred\n- Steps to reproduce\n- Any workaround already attempted',
    category: 'General',
    audience: 'all',
    tags: ['details', 'attachments', 'evidence', 'troubleshooting']
  }
];
