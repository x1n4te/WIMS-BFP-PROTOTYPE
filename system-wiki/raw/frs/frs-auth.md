Module 1: Authentication and Access Control
a. User Authentication
i.       Login with username and password (minimum 8 characters, including uppercase, lowercase, digit, and special character)  (Keycloak (Browser Flow))
ii.      Multi-Factor Authentication (MFA) required for System Administrators and National Validators (Keycloak Built-in OTP Policy)
·         MFA via Time-Based One-Time Password (TOTP) using authenticator app 
·         Option to remember trusted device for 7 days
iii.    Account lockout after 5 consecutive failed login attempts (Keycloak Brute Force Detection)
iv.    Automatic session timeout after 30 minutes of inactivity (Keycloak SSO Session Idle)
b. Password Management
i.        Reset password via secure email link with one-time token (expires after 15 minutes) (Keycloak "Forgot Password" Flow)
ii.      Change password for authenticated users (Keycloak Account Console)
·         Requires current password verification
·         Sends email notification upon successful password change
iii.    Enforce strong password policy (Keycloak Password Policies)
·         Minimum 8 characters
·         Must include uppercase letter, lowercase letter, digit, and special character
·         Password cannot match previous 3 passwords
·         Password expiry set to 90 days for administrative roles
c. Role-Based Access Control (RBAC)
i.        System shall support five (5) distinct user roles: (Keycloak Realm Roles)
o   Regional Encoder: Can create, edit, and upload incident records via the Regional Web Portal; resolve duplicates; access offline mode
o   National Validator: Can review and approve incident records; flag inconsistencies; no creation rights
o   National Analyst: Read-only access to aggregated data, statistical trends, and reports; cannot modify records
o   System Administrator: Full system access including user management, security monitoring, audit log review, and XAI threat analysis
o   Citizen: Can submit preliminary crowdsourced fire reports and securely view anonymized public heatmaps. 
ii.      Access permissions enforced through Keycloak Identity Provider (Python Keycloak + FastAPI Dependencies)
iii.    Least privilege principle applied – users can only access functions required for their role (React Guard Components)
iv.    Role assignment and modification restricted to System Administrators (Keycloak Admin Console)
d. Session Management
i.        Generate secure session token upon successful authentication (OIDC (OpenID Connect))
ii.      Session token stored securely in browser (httpOnly, secure, sameSite flags) (Browser Cookies / Memory)
iii.    Automatic session renewal on user activity (up to maximum session lifetime of 8 hours) (Keycloak Refresh Token)
iv.    Force logout on password change or role modification (Backchannel Logout)
v.      Support concurrent session detection with option to terminate previous session (Keycloak User Sessions)
