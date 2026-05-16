Module 13: Notification System
a. In-App Notifications
i.        System shall support real-time in-app notifications for: (Server-Sent Events (SSE))
o   Incident status updates (Draft → Pending → Validated)
o   Duplicate detection alerts
o   Manual verification decisions
o   Security alerts (for System Administrator)
o   Synchronization success/failure
ii.      Notifications shall appear as non-intrusive pop-up in top-right corner (react-hot-toast)
iii.    Users can view notification history in dedicated Notifications panel (Redis List (User Inbox))
b. Email Notifications
i.        System shall send email notifications for: (FastAPI Background Tasks)
o   Password reset requests
o   Account lockout warnings
o   Critical security alerts (for System Administrator)
o   Weekly summary reports (optional, configurable)
ii.      Email templates shall be professional and include: (Jinja2 + MJML)
·         BFP logo and branding
·         Clear subject line
·         Action required (if applicable)
·         Link to relevant system page
