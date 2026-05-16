Module 4: Data Commit and Immutable Storage
a. Commit and Store Process
i.        Once incident passes manual verification, system shall commit record to central database (FastAPI Dependency Injection)
ii.      Committed records shall be stored in append-only PostgreSQL table (PostgreSQL Permissions (GRANT/REVOKE))
·         No UPDATE or DELETE operations allowed on committed records
·         All modifications create new version entries with reference to original
iii.    Each committed record shall include: (Python hashlib + SQL Trigger)
·         SHA-256 cryptographic hash of entire incident data (for tamper detection)
·         Timestamp of commit operation
·         User ID of validator who approved the record
iv.    System shall generate “Insert Validated Record” transaction and send to Central Database (SQLAlchemy ORM)
v.      Central Database shall respond with “Write Result / DB Ack” confirmation (PostgreSQL RETURNING clause)
b. Audit Log Generation
i.        System shall log every commit operation in dedicated System Logs table (Partitioned PostgreSQL Table)
ii.      Audit log entry shall include: (Pydantic Middleware)
·         Incident ID
·         Commit timestamp
·         Validator user ID
·         SHA-256 hash of committed data
·         Synchronization status (online/offline)
iii.    Audit logs shall be immutable (append-only, no deletion) (PostgreSQL Rule (DO INSTEAD NOTHING))
iv.    System shall send “Log Import Success” message to System Logs data store (Asynchronous Message Queue)
