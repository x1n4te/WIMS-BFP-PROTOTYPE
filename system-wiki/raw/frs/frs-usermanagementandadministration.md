Module 12: User Management and Administration
a. User Onboarding
i.        System Administrator can create new user accounts (python-keycloak (Admin Client))
ii.      Required user information:
·         Full name
·         Email address (serves as username)
·         Role assignment (Encoder, Validator, Analyst, Administrator, Citizen)
·         Contact number (optional)
iii.    System shall auto-generate temporary password and send via secure email (Keycloak "Execute Actions")
iv.    User must change password upon first login (Required Action: Update Password)

b. User Profile Management
i.        Users can view and update their own profile information: (Keycloak Account API)
o   Full name
o   Email address
o   Contact number
ii.      Users cannot modify their own role assignment (only System Administrator can) (Keycloak Token Claims)
c. User Deactivation and Deletion
i.        System Administrator can deactivate user accounts (soft delete) (Keycloak enabled: false)
ii.      Deactivated accounts:
·         Cannot log in
·         Remain in database for audit purposes
·         Can be reactivated by System Administrator
iii.    Hard deletion of user accounts is not allowed (to preserve audit trail integrity) (PostgreSQL Foreign Keys)