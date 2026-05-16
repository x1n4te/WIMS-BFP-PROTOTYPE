Module 2: Offline-First Incident Management
a. Incident Data Entry
i.        Regional Encoder can create new fire incident reports with the following fields: (React Hook Form + Zod)
o   Incident ID (auto-generated, immutable) (UUID (v4))
o   Date and time of incident (timestamp)
o   Location (address, municipality, province)
o   Incident type (structure fire, vehicular fire, grass fire, others)
o   Incident narrative (free-text description)
o   Casualties (injuries, fatalities)
o   Property damage estimate
o   Responders deployed
o   Fire suppression status (ongoing, contained, extinguished)
ii.      Support file attachments (photos, reports, maps) (React Dropzone)
·         Accepted formats: .jpg, .png, .pdf, .docx (max 10MB each)
·         Maximum 5 attachments per incident
·         Attachments encrypted before storage (Web Crypto API (AES-GCM))
iii.    Incident form shall include client-side validation
·         Required fields: Incident ID, date/time, location, incident type, narrative
·         Real-time validation feedback (field-level error messages)
b. Offline Data Capture and Storage
i.        System shall detect network availability automatically (Navigator API + React Hook)
ii.      When offline, incident data shall be stored locally in browser IndexedDB (Dexie.js (IndexedDB Wrapper))
iii.    Offline-captured records shall be encrypted using AES-256-GCM before local storage (Web Crypto + ArrayBuffer)
iv.    User interface shall display clear “Offline Mode” indicator (Tailwind CSS / Toast)
v.      All CRUD operations (Create, Read, Update, Delete) must function fully in offline mode
vi.    Offline storage capacity: minimum 1,000 incident records with attachments (StorageManager API)
c. Data Synchronization
i.        System shall automatically detect network restoration (TanStack Query (React Query))
ii.      Upon reconnection, system shall: (Background Sync API (Service Worker))
·         Upload locally stored incidents to central server
·         Verify cryptographic integrity of each record (AES-256-GCM tag check)
·         Detect and resolve conflicts (duplicate incident detection) 
·         Update local database with server response
iii.    Synchronization process must be atomic (all-or-nothing per incident) (FastAPI transaction.atomic)
iv.    Failed synchronization attempts shall retry automatically (exponential backoff, max 5 retries) (TanStack Query retry)
v.     User shall receive notification of synchronization success or failure (React Hot Toast)

d. Incident Status Tracking
i.        System shall support the following incident statuses: (PostgreSQL Enum)
o   Draft: Incomplete record, saved locally, not yet submitted
o   Pending: Submitted for validation, awaiting National Validator review
o   Validated: Approved by National Validator, committed to central database
o   Flagged: Potential duplicate or data integrity issue, requires manual verification
o   Rejected: Did not pass validation, returned to encoder with reason
ii.      Status transitions shall be logged with timestamp and user ID (FastAPI Middleware / SQL Triggers)
iii.    Regional Encoder can view history of status changes for each incident (React Timeline Component)
