Module 10: Compliance and Data Privacy
a. Data Privacy Act (RA 10173) Compliance
i.        System shall implement data minimization principle
o   Collect only necessary data for fire incident reporting
o   Do not collect Sensitive Personal Information (SPI) unless operationally required
ii.      System shall provide purpose limitation
·         Incident data used only for fire suppression operations and national statistics
·         Secondary use of data is strictly prohibited without explicit consent
iii.    System shall support individual rights
·         Right to access: Users can request copy of their submitted incidents
·         Right to rectification: Users can request correction of inaccurate data
·         Right to erasure: Users can request deletion (soft delete with audit trail)
b. Cloud-Based Data Protection Impact Assessment (DPIA)
i.        System shall maintain DPIA documentation covering: 
o   Description of data processing activities within the Docker/VPS environment.
o   Identified privacy risks (e.g., cloud-based data exposure) and mitigation measures.
o   Legal basis for processing (public interest / official authority)
o   Data retention periods
ii.      DPIA shall be reviewed annually or whenever major infrastructure changes.
c. Records of Processing Activities (RoPA)
i.        System shall maintain RoPA documenting:
o   Categories of data subjects (Regional Encoders, Validators, Analysts, Administrators, Citizens)
o   Categories of personal data (names, user IDs, email addresses, login timestamps)
o   Purposes of processing (incident reporting, access control, audit logging)
o   Data retention periods (active records: indefinite; audit logs: 7 years)
o   Security measures (encryption, access control, audit logging)
ii.      RoPA shall be accessible to System Administrator and Data Protection Officer
d. Breach Notification
i.        In the event of data breach, system shall:
o   Automatically generate breach notification report
o   Include details: date/time of breach, affected data categories, estimated number of affected records
o   Notify Data Protection Officer and System Administrator immediately
ii.      System Administrator shall assess breach severity and determine if National Privacy Commission (NPC) notification is required (within 72 hours if confirmed)
