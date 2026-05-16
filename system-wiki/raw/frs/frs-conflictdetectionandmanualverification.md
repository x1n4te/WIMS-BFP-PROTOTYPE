Module 3: Conflict Detection and Manual Verification
a. Duplicate Detection
i.        System shall automatically compare newly uploaded incidents against existing records in the central database (FastAPI Background Tasks)
ii.      Conflict detection algorithm shall check for: (Python RapidFuzz + SQL Intervals)
·         Exact match of incident location and date/time (within 30-minute window)
·         Similarity of incident narrative (using fuzzy string matching, threshold 80%)
·         Matching casualty counts and property damage estimates
iii.    When potential duplicate is detected: (PostgreSQL Status Update)
·         Mark incident status as “Flagged”
·         Generate “Potential Duplicate Alert” with comparison details
·         Route to Manual Verification queue
b. Manual Verification Workflow
i.       National Validator shall review flagged incidents in dedicated queue (React Table + React Query)
ii.      System shall display side-by-side comparison of conflicting records: (react-diff-viewer-continued)
·         Incident ID, date/time, location 
·         Narrative text (with highlighted differences)
·         Casualty and damage data
·         Attachments (if any)
iii.    National Validator actions: (FastAPI RPC-style Endpoints)
·         Confirm as Duplicate: Merge records, retain only one in database, log merge action
·         Confirm as Unique: Clear “Flagged” status, approve for storage
·         Request Revision: Return to Regional Encoder with specific instructions
iv.    Regional Encoder shall be notified of verification decision via in-app notification (Server-Sent Events (SSE))
v.     Regional Encoder can view comparison details and provide clarification if requested
c. Revision and Resubmission 
i.       If incident is returned for revision: (sqlalchemy-continuum)
o   Regional Encoder receives notification with reason for return
o   Encoder can edit incident details and resubmit
o   System logs revision history (original version preserved)
ii.      Resubmitted incident re-enters validation queue with “Resubmitted” tag (PostgreSQL Tags Column)
iii.     National Validator can view revision history before making final decision (React Timeline Component)
