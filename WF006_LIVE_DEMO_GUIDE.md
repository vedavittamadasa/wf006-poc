# WF-006 Proof of Concept: Complete Live Demonstration Master Guide

**Project Name:** WF-006 — CRM / DBMS / Data Governance Shared Data Backbone  
**GCP Project ID:** `project-225be79a-d654-49e1-950`  
**Region:** `us-central1`  
**Live Swagger 1 (Validator & Persistence):** [https://wf006-cloudrun-662300223067.us-central1.run.app/docs](https://wf006-cloudrun-662300223067.us-central1.run.app/docs)  
**Live Swagger 2 (DND Governance):** [https://wf006-dnd-service-662300223067.us-central1.run.app/docs](https://wf006-dnd-service-662300223067.us-central1.run.app/docs)  
**Target Audience:** Architects, Leadership, Engineering Teams, Stakeholders  

---

## 📋 Table of Contents
1. [⚠️ CRITICAL FIRST STEP: Cloud Shell Initialization (Do NOT Skip)](#1-critical-first-step-cloud-shell-initialization-do-not-skip)
2. [Demo Flow Diagram (The Architecture Story)](#2-demo-flow-diagram-the-architecture-story)
3. [Section 1: Interactive Swagger API Demonstration (All Endpoints & Payloads)](#3-section-1-interactive-swagger-api-demonstration-all-endpoints--payloads)
   - [Service A: Contact Ingestion, Validation & Persistence Service](#service-a-contact-ingestion-validation--persistence-service)
     - [`GET /health`](#endpoint-a1-get-health)
     - [`POST /validate` (Valid Contact)](#endpoint-a2-post-validate-clean-valid-contact)
     - [`POST /validate` (Missing Required Fields)](#endpoint-a3-post-validate-rejected---missing-mandatory-fields)
     - [`POST /validate` (Missing Phone and Email)](#endpoint-a4-post-validate-rejected---unreachable-contact)
     - [`POST /persist` (Direct Master Database Write)](#endpoint-a5-post-persist-direct-master-database-write)
     - [`POST /audit-log` (Direct Governance Decision Logging)](#endpoint-a6-post-audit-log-direct-governance-audit-logging)
     - [`GET /contacts` (Fetch Live Master Contacts)](#endpoint-a7-get-contacts-fetch-live-master-contacts)
     - [`GET /audit-logs` (Fetch Live Audit Trail)](#endpoint-a8-get-audit-logs-fetch-live-audit-trail)
   - [Service B: Dedicated DND Governance Service](#service-b-dedicated-dnd-governance-service)
     - [`GET /health`](#endpoint-b1-get-health)
     - [`POST /check-dnd` (Approved Devotee)](#endpoint-b2-post-check-dnd-clean-contact-approved)
     - [`POST /check-dnd` (Blocked by Explicit DND Flag)](#endpoint-b3-post-check-dnd-blocked-by-explicit-dnd-flag)
     - [`POST /check-dnd` (Blocked by Revoked Consent)](#endpoint-b4-post-check-dnd-blocked-by-revoked-consent)
     - [`POST /check-dnd` (Blocked by Suppression Registry)](#endpoint-b5-post-check-dnd-blocked-by-suppression-registry)
4. [Section 2: Live Orchestration with Google Cloud Workflows](#4-section-2-live-orchestration-with-google-cloud-workflows)
   - [Test Run 1: Approved Devotee (Full Persistence Path)](#test-run-1-approved-devotee-full-persistence-path)
   - [Test Run 2: Blocked Devotee (Audit Log Only Path)](#test-run-2-blocked-devotee-audit-log-only-path)
5. [Section 3: Transactional Master Database (Cloud SQL PostgreSQL)](#5-section-3-transactional-master-database-cloud-sql-postgresql)
6. [Section 4: Real-Time CDC Data Replication (Datastream)](#6-section-4-real-time-cdc-data-replication-datastream)
7. [Section 5: Live Analytics & Dashboards (BigQuery)](#7-section-5-live-analytics--dashboards-bigquery)
8. [Presenter's Verbal Script: Exactly What to Say at Each Step](#8-presenters-verbal-script-exactly-what-to-say-at-each-step)
9. [Answers to Tough Questions Leadership Might Ask](#9-answers-to-tough-questions-leadership-might-ask)

---

## 1. ⚠️ CRITICAL FIRST STEP: Cloud Shell Initialization (Do NOT Skip)

Whenever Google Cloud Shell opens, reconnects, or times out, it starts with **no active project**. Running commands without setting the project causes the dreaded error:
`ERROR: (gcloud...) Error parsing [stream]. Failed to find attribute [project].`

### Run These 3 Commands Immediately in Cloud Shell:
```bash
# Step 1: Set the exact project ID
gcloud config set project project-225be79a-d654-49e1-950

# Step 2: Set default compute region
gcloud config set compute/region us-central1

# Step 3: Check Datastream CDC Status (Must return RUNNING)
gcloud datastream streams describe wf006-stream --location=us-central1 --format="value(state)"
```

> **Quick Fix if Datastream is `PAUSED`:**
> ```bash
> gcloud datastream streams update wf006-stream --location=us-central1 --state=RUNNING
> ```

Once the above returns `RUNNING`, your terminal is 100% ready and will never error out.

---

## 2. Demo Flow Diagram (The Architecture Story)

Share your screen or explain this 30-second architecture overview:

```text
Incoming Contact Event (CRM / CSV / WhatsApp / DCC)
                        │
                        ▼
   Google Cloud Workflows Orchestrator (`wf006-orchestrator`)
                        │
       ┌────────────────┴────────────────┐
       ▼                                 ▼
1. Cloud Run Validator            2. Cloud Run DND Service
   `/validate`                       `/check-dnd`
   (Validates schema, fields,        (Checks suppression lists,
    phone/email format, owner)        explicit DND, consent status)
       └────────────────┬────────────────┘
                        │
       Decision Branching in Workflow:
       ├── If DND = FALSE ──▶ Route to `/persist`   ──▶ Writes to Cloud SQL master table
       └── If DND = TRUE  ──▶ Route to `/audit-log` ──▶ Excludes from outreach; logs audit
                        │
                        ▼
       Cloud SQL PostgreSQL (`wf006-postgres`)
       Master Database & Write-Ahead Log (WAL)
                        │
                        ▼
       Google Cloud Datastream CDC (`wf006-stream`)
       Real-Time, Continuous Change Data Capture (Zero ETL)
                        │
                        ▼
       Google BigQuery (`public.contacts` & `wf006_analytics`)
       - Raw streaming replica with Datastream CDC metadata UUIDs
       - Analytical views for compliance & executive Looker dashboards
```

---

## 3. Section 1: Interactive Swagger API Demonstration (All Endpoints & Payloads)

Demonstrating directly via Swagger UI is the most professional and visually impressive way to show live APIs. Audiences see the real HTTP requests, JSON bodies, and status codes.

Open these two tabs in your browser side-by-side:
- **Tab 1 (Validator & Storage):** `https://wf006-cloudrun-662300223067.us-central1.run.app/docs`
- **Tab 2 (DND Governance Gate):** `https://wf006-dnd-service-662300223067.us-central1.run.app/docs`

---

### Service A: Contact Ingestion, Validation & Persistence Service
👉 **Swagger URL:** [https://wf006-cloudrun-662300223067.us-central1.run.app/docs](https://wf006-cloudrun-662300223067.us-central1.run.app/docs)

---

#### Endpoint A1: `GET /health`
- **What you are doing:** Checking the health of the core ingestion microservice.
- **Why you are doing it:** Proves the service is running live on Cloud Run and actively connected to Cloud SQL PostgreSQL.
- **How to execute:**
  1. Click on `GET /health`.
  2. Click **Try it out** ➔ **Execute**.
- **Expected Response (HTTP 200):**
  ```json
  {
    "service": "wf006-cloudrun",
    "status": "healthy",
    "database_backend": "PostgreSQL",
    "timestamp": "2026-10-04T09:30:00.000Z"
  }
  ```
- **What to say:** *"You can see our microservice is healthy and successfully connected to Cloud SQL PostgreSQL backend."*

---

#### Endpoint A2: `POST /validate` (Clean, Valid Contact)
- **What you are doing:** Sending a complete, properly formatted devotee contact for validation.
- **Why you are doing it:** Demonstrates business schema enforcement. Every incoming contact must have `Contact_ID`, `source`, `owner`, and a valid reachable channel.
- **How to execute:**
  1. Click `POST /validate`.
  2. Click **Try it out**.
  3. Paste this payload into the **Request body**:
     ```json
     {
       "Contact_ID": "CNT-SWAGGER-DEMO-01",
       "name": "Radha Raman Das",
       "phone": "+919876543210",
       "email": "radha.raman@example.org",
       "source": "CRM",
       "owner": "seva-outreach-team",
       "consent_status": "GRANTED",
       "dnd_status": false
     }
     ```
  4. Click **Execute**.
- **Expected Response (HTTP 200 OK):**
  ```json
  {
    "status": "SUCCESS",
    "is_valid": true,
    "contact": {
      "Contact_ID": "CNT-SWAGGER-DEMO-01",
      "name": "Radha Raman Das",
      "phone": "+919876543210",
      "email": "radha.raman@example.org",
      "source": "CRM",
      "owner": "seva-outreach-team",
      "consent_status": "GRANTED",
      "dnd_status": false,
      "created_at": "2026-10-04T09:31:00.000Z",
      "updated_at": "2026-10-04T09:31:00.000Z"
    },
    "validation_timestamp": "2026-10-04T09:31:00.000Z",
    "message": "Contact passed all schema and mandatory attribute validations."
  }
  ```
- **What to say:** *"The validator confirmed that all required attributes are present and formatted correctly."*

---

#### Endpoint A3: `POST /validate` (Rejected - Missing Mandatory Fields)
- **What you are doing:** Sending a corrupt/incomplete record missing `source` and `owner`.
- **Why you are doing it:** Proves that corrupt data from external sources cannot leak into our master database.
- **How to execute:**
  1. In `POST /validate`, paste this payload:
     ```json
     {
       "Contact_ID": "CNT-SWAGGER-BAD-01",
       "name": "Incomplete Donor Record",
       "phone": "+919811122233"
     }
     ```
  2. Click **Execute**.
- **Expected Response (HTTP 422 Unprocessable Entity):**
  ```json
  {
    "detail": [
      {
        "type": "missing",
        "loc": ["body", "source"],
        "msg": "Field required",
        "input": { ... }
      },
      {
        "type": "missing",
        "loc": ["body", "owner"],
        "msg": "Field required",
        "input": { ... }
      }
    ]
  }
  ```
- **What to say:** *"Notice the API instantly rejects the request with HTTP 422. Under WF-006 rules, an unowned or unsourced contact is never accepted."*

---

#### Endpoint A4: `POST /validate` (Rejected - Unreachable Contact)
- **What you are doing:** Sending a contact with valid metadata, but missing *both* phone and email.
- **Why you are doing it:** Proves business rule validation: a contact record is useless if we have no channel to reach the devotee.
- **How to execute:**
  1. In `POST /validate`, paste this payload:
     ```json
     {
       "Contact_ID": "CNT-SWAGGER-BAD-02",
       "name": "Ghost Devotee",
       "source": "CSV",
       "owner": "seva-outreach-team"
     }
     ```
  2. Click **Execute**.
- **Expected Response (HTTP 422 Unprocessable Entity):**
  ```json
  {
    "detail": "Contact must include at least a phone number or an email address."
  }
  ```
- **What to say:** *"Our custom validator ensures that at least one communication channel (phone or email) is provided before moving forward."*

---

#### Endpoint A5: `POST /persist` (Direct Master Database Write)
- **What you are doing:** Calling the persistence endpoint that inserts the approved contact into Cloud SQL PostgreSQL.
- **Why you are doing it:** Shows how the service performs an ACID transaction, writing to both the master `contacts` table and the `contact_audit_log` table.
- **How to execute:**
  1. Click `POST /persist`.
  2. Click **Try it out**.
  3. Paste this payload:
     ```json
     {
       "Contact_ID": "CNT-SWAGGER-PERSIST-01",
       "name": "Balarama Dasa",
       "phone": "+919876599999",
       "email": "balarama@example.org",
       "source": "CRM",
       "owner": "seva-outreach-team",
       "consent_status": "GRANTED",
       "dnd_status": false
     }
     ```
  4. Click **Execute**.
- **Expected Response (HTTP 200 OK):**
  ```json
  {
    "status": "PERSISTED",
    "contact_id": "CNT-SWAGGER-PERSIST-01",
    "storage": "Cloud SQL PostgreSQL",
    "message": "Master record and audit log saved to Cloud SQL."
  }
  ```
- **What to say:** *"This confirms the contact is written to Cloud SQL PostgreSQL. In addition, an audit record was written atomically in the same transaction."*

---

#### Endpoint A6: `POST /audit-log` (Direct Governance Audit Logging)
- **What you are doing:** Recording a compliance decision for a blocked contact without writing it to the master outreach table.
- **Why you are doing it:** Shows that even when a devotee is blocked by DND, we maintain a complete, immutable audit trail for legal compliance.
- **How to execute:**
  1. Click `POST /audit-log`.
  2. Click **Try it out**.
  3. Paste this payload:
     ```json
     {
       "contact_id": "CNT-SWAGGER-BLOCKED-01",
       "decision": "BLOCKED",
       "reason": "Devotee requested DND opt-out via WhatsApp",
       "details": {
         "channel": "WhatsApp",
         "opt_out_timestamp": "2026-10-04T09:35:00Z"
       }
     }
     ```
  4. Click **Execute**.
- **Expected Response (HTTP 200 OK):**
  ```json
  {
    "status": "AUDIT_LOGGED",
    "contact_id": "CNT-SWAGGER-BLOCKED-01",
    "storage": "Cloud SQL"
  }
  ```
- **What to say:** *"The blocked contact is excluded from outreach, but the audit entry is securely stored in Cloud SQL for compliance reporting."*

---

#### Endpoint A7: `GET /contacts` (Fetch Live Master Contacts)
- **What you are doing:** Retrieving all active master contacts stored in the database.
- **Why you are doing it:** Proves the records submitted earlier are genuinely stored in the PostgreSQL database.
- **How to execute:**
  1. Click `GET /contacts`.
  2. Click **Try it out** ➔ **Execute**.
- **Expected Response (HTTP 200 OK):**
  A JSON array containing the master contacts, with your newly inserted records visible at the top.
- **What to say:** *"Here you can see our live master contacts list queried directly from Cloud SQL PostgreSQL."*

---

#### Endpoint A8: `GET /audit-logs` (Fetch Live Audit Trail)
- **What you are doing:** Retrieving the immutable governance audit log records.
- **Why you are doing it:** Proves compliance transparency.
- **How to execute:**
  1. Click `GET /audit-logs`.
  2. Click **Try it out** ➔ **Execute**.
- **Expected Response (HTTP 200 OK):**
  A JSON array showing every `APPROVED` and `BLOCKED` decision along with reasons and timestamps.

---

### Service B: Dedicated DND Governance Service
👉 **Swagger URL:** [https://wf006-dnd-service-662300223067.us-central1.run.app/docs](https://wf006-dnd-service-662300223067.us-central1.run.app/docs)

🗣️ **Key Architect Pitch to Audience:**  
> *"Notice that DND checking is completely decoupled into its own independent microservice. In our enterprise architecture, this DND Governance Service acts as an impartial compliance gatekeeper that cannot be bypassed by any outreach workflow."*

---

#### Endpoint B1: `GET /health`
- **What you are doing:** Checking the health of the DND Governance microservice and suppression list count.
- **How to execute:** Click `GET /health` ➔ **Try it out** ➔ **Execute**.
- **Expected Response (HTTP 200):**
  ```json
  {
    "service": "wf006-dnd-service",
    "status": "healthy",
    "suppression_registry_count": 7,
    "timestamp": "2026-10-04T09:40:00.000Z"
  }
  ```

---

#### Endpoint B2: `POST /check-dnd` (Clean Contact -> APPROVED)
- **What you are doing:** Checking a devotee with clean consent and active permission.
- **Why you are doing it:** Shows the green path where a devotee is cleared for outreach.
- **How to execute:**
  1. Click `POST /check-dnd` ➔ **Try it out**.
  2. Paste this payload:
     ```json
     {
       "Contact_ID": "CNT-CLEAN-01",
       "phone": "+919876500001",
       "email": "clean.devotee@example.org",
       "consent_status": "GRANTED",
       "dnd_status": false
     }
     ```
  3. Click **Execute**.
- **Expected Response (HTTP 200 OK):**
  ```json
  {
    "Contact_ID": "CNT-CLEAN-01",
    "is_dnd": false,
    "action": "ALLOW",
    "reason": "Contact is verified and not on any suppression lists",
    "checked_at": "2026-10-04T09:41:00.000Z"
  }
  ```

---

#### Endpoint B3: `POST /check-dnd` (Blocked by Explicit DND Flag)
- **What you are doing:** Verifying an incoming payload that has `dnd_status: true`.
- **Why you are doing it:** Shows that if a devotee previously asked to not be disturbed, the governance gate respects it immediately.
- **Payload:**
  ```json
  {
    "Contact_ID": "CNT-DND-FLAG-01",
    "phone": "+919811100000",
    "email": "optout@example.com",
    "consent_status": "PENDING",
    "dnd_status": true
  }
  ```
- **Expected Response (HTTP 200 OK):**
  ```json
  {
    "Contact_ID": "CNT-DND-FLAG-01",
    "is_dnd": true,
    "action": "BLOCK",
    "reason": "Payload contains explicit dnd_status=true",
    "checked_at": "2026-10-04T09:42:00.000Z"
  }
  ```

---

#### Endpoint B4: `POST /check-dnd` (Blocked by Revoked Consent)
- **What you are doing:** Verifying a contact where `consent_status: "REVOKED"`.
- **Why you are doing it:** Enforces DPDP Act and GDPR compliance. When consent is revoked, outreach is illegal.
- **Payload:**
  ```json
  {
    "Contact_ID": "CNT-REVOKED-01",
    "phone": "+919822233344",
    "email": "revoked@example.com",
    "consent_status": "REVOKED",
    "dnd_status": false
  }
  ```
- **Expected Response (HTTP 200 OK):**
  ```json
  {
    "Contact_ID": "CNT-REVOKED-01",
    "is_dnd": true,
    "action": "BLOCK",
    "reason": "Consent status is REVOKED by user",
    "checked_at": "2026-10-04T09:43:00.000Z"
  }
  ```

---

#### Endpoint B5: `POST /check-dnd` (Blocked by Suppression Registry)
- **What you are doing:** Sending a contact who claims `dnd_status: false`, but whose phone number `+919999999999` is registered in our suppression blacklist.
- **Why you are doing it:** Demonstrates central governance enforcement. Even if an external CRM sends `dnd_status: false`, our central registry overrides it and protects the organization.
- **Payload:**
  ```json
  {
    "Contact_ID": "CNT-SUPPRESSION-CHECK",
    "phone": "+919999999999",
    "email": "tricky.lead@example.com",
    "consent_status": "GRANTED",
    "dnd_status": false
  }
  ```
- **Expected Response (HTTP 200 OK):**
  ```json
  {
    "Contact_ID": "CNT-SUPPRESSION-CHECK",
    "is_dnd": true,
    "action": "BLOCK",
    "reason": "Phone number +919999999999 is listed in the DND suppression registry",
    "checked_at": "2026-10-04T09:44:00.000Z"
  }
  ```
- **What to say:** *"Notice that even though the incoming source marked this lead as `dnd_status: false`, our DND governance microservice detected the blacklisted phone number and blocked it."*

---

### Service C: Live POC Integrations & Verification (100% Inside Swagger UI)
👉 **Swagger URL:** [https://wf006-cloudrun-662300223067.us-central1.run.app/docs](https://wf006-cloudrun-662300223067.us-central1.run.app/docs) (Tag: **Live POC Integrations & Verification**)

🗣️ **Key Pitch to Leadership:**  
> *"We have exposed live integration endpoints right in our Swagger contract. This allows anyone to verify Pub/Sub asynchronous event buffering, Google Cloud Workflows state machine execution, Datastream CDC continuous replication, and BigQuery analytics live from a single browser screen with zero CLI commands!"*

---

#### Integration 1: `POST /demo/publish-pubsub` (Asynchronous Event Ingestion)
- **What you are doing:** Publishing a contact registration event into Google Cloud Pub/Sub topic `wf006-contact-topic`.
- **Why you are doing it:** Proves event-driven decoupling. When high traffic surges occur (e.g. Janmashtami registrations), the system buffers events in Pub/Sub without hammering the transactional database.
- **Payload:**
  ```json
  {
    "Contact_ID": "CNT-PUBSUB-DEMO-01",
    "name": "Gauranga Dasa",
    "phone": "+919876543210",
    "email": "gauranga@example.org",
    "source": "WhatsApp",
    "owner": "seva-outreach-team",
    "consent_status": "GRANTED",
    "dnd_status": false
  }
  ```
- **Expected Response (HTTP 200 OK):**
  ```json
  {
    "status": "PUBLISHED",
    "topic": "projects/project-225be79a-d654-49e1-950/topics/wf006-contact-topic",
    "subscription": "projects/project-225be79a-d654-49e1-950/subscriptions/wf006-contact-sub",
    "message_id": "pubsub-msg-e4a8b71d234c",
    "publish_time": "2026-10-04T10:00:00.000Z",
    "explanation": "Event accepted at the ingestion edge and queued in GCP Pub/Sub buffer without blocking transactional database."
  }
  ```

---

#### Integration 2: `POST /demo/trigger-workflow` (Central Workflows Orchestration)
- **What you are doing:** Triggering the complete `wf006-orchestrator` state machine directly from Swagger.
- **Why you are doing it:** Shows the end-to-end pipeline in 1 click: Schema Validation ➔ DND Governance Query ➔ Automatic Branching ➔ Cloud SQL Master Write.
- **Payload (Approved Devotee):**
  ```json
  {
    "contact": {
      "Contact_ID": "CNT-WF-DEMO-01",
      "name": "Sri Nityananda Dasa",
      "phone": "+919876511111",
      "email": "nityananda@example.org",
      "source": "CRM",
      "owner": "seva-outreach-team",
      "consent_status": "GRANTED",
      "dnd_status": false
    }
  }
  ```
- **Expected Response (HTTP 200 OK):**
  ```json
  {
    "workflow_name": "wf006-orchestrator",
    "execution_id": "wf-exec-a82f3b1c",
    "status": "APPROVED",
    "branch_taken": "persist_master_contact",
    "contact_id": "CNT-WF-DEMO-01",
    "persistence_status": "PERSISTED",
    "storage_backend": "Cloud SQL PostgreSQL",
    "message": "Contact validated, cleared DND governance, and stored in master database."
  }
  ```
- **Payload (Blocked Devotee - Suppression List Interception):**
  ```json
  {
    "contact": {
      "Contact_ID": "CNT-WF-BLOCKED-01",
      "name": "Kishore Kumar",
      "phone": "+919999999999",
      "email": "kkumar@example.net",
      "source": "WhatsApp",
      "owner": "seva-outreach-team",
      "consent_status": "PENDING",
      "dnd_status": false
    }
  }
  ```
- **Expected Response (HTTP 200 OK):**
  ```json
  {
    "workflow_name": "wf006-orchestrator",
    "execution_id": "wf-exec-f91b42ce",
    "status": "BLOCKED",
    "branch_taken": "audit_log_only",
    "contact_id": "CNT-WF-BLOCKED-01",
    "persistence_status": "EXCLUDED",
    "message": "Contact excluded from master outreach table; logged in immutable audit trail."
  }
  ```

---

#### Integration 3: `GET /demo/datastream-cdc-status` (Real-Time CDC Replication Status)
- **What you are doing:** Checking the live status of Google Cloud Datastream CDC.
- **Why you are doing it:** Proves the zero-ETL real-time replication pipeline is active between Cloud SQL PostgreSQL (source) and BigQuery (destination).
- **Action:** Click `GET /demo/datastream-cdc-status` ➔ **Try it out** ➔ **Execute**.
- **Expected Response (HTTP 200 OK):**
  ```json
  {
    "datastream_name": "wf006-stream",
    "gcp_project": "project-225be79a-d654-49e1-950",
    "region": "us-central1",
    "state": "RUNNING",
    "cdc_architecture": {
      "source": {
        "engine": "Cloud SQL PostgreSQL 15",
        "instance": "wf006-postgres",
        "replication_slot": "wf006_datastream_slot",
        "mechanism": "pgoutput logical decoding (WAL)"
      },
      "destination": {
        "engine": "Google BigQuery",
        "dataset": "public",
        "target_table": "public.contacts",
        "cdc_metadata_column": "datastream_metadata (UUID + source_timestamp)"
      }
    },
    "latency": "sub-minute (near real-time)"
  }
  ```

---

#### Integration 4: `GET /demo/bigquery-synced-contacts` (BigQuery Replicated Data)
- **What you are doing:** Inspecting the synchronized records inside Google BigQuery.
- **Why you are doing it:** Shows that committed PostgreSQL records exist in BigQuery with their Datastream CDC metadata UUIDs.
- **Action:** Click `GET /demo/bigquery-synced-contacts` ➔ **Try it out** ➔ **Execute**.
- **Expected Response (HTTP 200 OK):**
  A JSON list showing master contacts along with their `datastream_metadata` objects containing `uuid` and `source_timestamp`.

---

#### Integration 5: `GET /demo/bigquery-compliance-metrics` (Looker Analytics Views)
- **What you are doing:** Querying the compliance analytics model (`v_source_compliance_metrics`).
- **Why you are doing it:** Demonstrates the BI layer that drives Looker Studio executive dashboards.
- **Action:** Click `GET /demo/bigquery-compliance-metrics` ➔ **Try it out** ➔ **Execute**.
- **Expected Response (HTTP 200 OK):**
  Returns source breakdown (`CRM`, `CSV`, `WhatsApp`, `DCC`) with total counts, approved counts, DND blocked counts, and DND blocked percentage!

---

#### Integration 6: `GET /demo/api-gateway-contract` (API Gateway Routing Spec)
- **What you are doing:** Viewing the API Gateway configuration contract.
- **Why you are doing it:** Explains that Swagger is not just a UI; it is the official OpenAPI 3.0 specification imported into Google Cloud API Gateway for TLS enforcement and 100 req/sec rate limiting.
- **Action:** Click `GET /demo/api-gateway-contract` ➔ **Try it out** ➔ **Execute**.

---

## 4. Section 2: Live Orchestration with Google Cloud Workflows

Now run **Google Cloud Workflows (`wf006-orchestrator`)** to show how it coordinates both microservices and automatically branches based on the DND decision.

> [!TIP]
> **Windows PowerShell vs Linux / Cloud Shell:**  
> On Windows PowerShell, single quotes `'...'` in inline JSON cause parse errors.  
> To prevent any quoting issues, **use the `@payload-approved.json` file approach** shown below! It works 100% reliably on Windows, Mac, and Linux.

---

### Test Run 1: Approved Devotee (Full Persistence Path)

#### Option A: Using the Payload File (Recommended for Windows PowerShell / CMD):
```powershell
gcloud workflows run wf006-orchestrator --location=us-central1 --data=@payload-approved.json
```

#### Option B: Inline Command for Linux / Cloud Shell:
```bash
gcloud workflows run wf006-orchestrator \
    --location=us-central1 \
    --data='{"contact":{"Contact_ID":"DEMO-001-APPROVED","name":"Radha Raman Das","phone":"+919876500001","email":"radha.raman@example.org","source":"CRM","owner":"seva-outreach-team","consent_status":"GRANTED","dnd_status":false}}'
```

#### Option C: Inline Command for Windows PowerShell:
```powershell
gcloud workflows run wf006-orchestrator --location=us-central1 --% --data="{\"contact\":{\"Contact_ID\":\"DEMO-001-APPROVED\",\"name\":\"Radha Raman Das\",\"phone\":\"+919876500001\",\"email\":\"radha.raman@example.org\",\"source\":\"CRM\",\"owner\":\"seva-outreach-team\",\"consent_status\":\"GRANTED\",\"dnd_status\":false}}"
```

- **Output on Screen:**
  ```json
  {
    "status": "APPROVED",
    "contact_id": "DEMO-001-APPROVED",
    "persistence_status": "PERSISTED",
    "message": "Contact validated, cleared DND, and written to Cloud SQL master."
  }
  ```
- **What to say:** *"The workflow called the Validator, verified DND compliance, branched to the persist step, and stored Radha Raman Das into Cloud SQL PostgreSQL."*

---

### Test Run 2: Blocked Devotee (Audit Log Only Path)

#### Option A: Using the Payload File (Recommended for Windows PowerShell / CMD):
```powershell
gcloud workflows run wf006-orchestrator --location=us-central1 --data=@payload-blocked.json
```

#### Option B: Inline Command for Linux / Cloud Shell:
```bash
gcloud workflows run wf006-orchestrator \
    --location=us-central1 \
    --data='{"contact":{"Contact_ID":"DEMO-002-BLOCKED","name":"Kishore Kumar","phone":"+919999999999","email":"kkumar@example.net","source":"WhatsApp","owner":"seva-outreach-team","consent_status":"PENDING","dnd_status":false}}'
```

#### Option C: Inline Command for Windows PowerShell:
```powershell
gcloud workflows run wf006-orchestrator --location=us-central1 --% --data="{\"contact\":{\"Contact_ID\":\"DEMO-002-BLOCKED\",\"name\":\"Kishore Kumar\",\"phone\":\"+919999999999\",\"email\":\"kkumar@example.net\",\"source\":\"WhatsApp\",\"owner\":\"seva-outreach-team\",\"consent_status\":\"PENDING\",\"dnd_status\":false}}"
```

- **Output on Screen:**
  ```json
  {
    "status": "BLOCKED",
    "contact_id": "DEMO-002-BLOCKED",
    "reason": "Phone number +919999999999 is listed in the DND suppression registry",
    "action_taken": "Excluded from master outreach table; logged in audit log."
  }
  ```
- **What to say:** *"Because the phone number was on the suppression registry, the workflow automatically branched away from the master table and logged an immutable audit entry."*

---

## 5. Section 3: Transactional Master Database (Cloud SQL PostgreSQL)

Show that records are stored in PostgreSQL. Run this in Cloud Shell:

```bash
# Query the live contacts endpoint
curl -s "https://wf006-cloudrun-662300223067.us-central1.run.app/contacts" | python3 -m json.tool | head -n 30
```

- **What to say:** *"Here is the raw query output showing the contacts safely persisted in Cloud SQL PostgreSQL."*

---

## 6. Section 4: Real-Time CDC Data Replication (Datastream)

🗣️ **Key Enterprise Pitch to Audience:**  
> *"In legacy systems, people run batch ETL jobs at midnight that take hours and lock tables. In our modern architecture, Google Cloud Datastream performs Change Data Capture (CDC) directly from the PostgreSQL Write-Ahead Log into BigQuery with sub-minute latency and zero database performance degradation."*

### Show CDC Stream State in Cloud Shell:
```bash
gcloud datastream streams describe wf006-stream --location=us-central1 --format="value(state)"
```
*(Confirms `RUNNING`)*

### Verify the Replicated Rows in BigQuery:
```bash
bq query --use_legacy_sql=false \
  'SELECT contact_id, name, phone, source, owner, datastream_metadata FROM `public.contacts` ORDER BY created_at DESC LIMIT 5;'
```

- **What to Point to on Screen:**
  Show the row and highlight the `datastream_metadata` column:
  ```json
  {
    "uuid": "62a940bc-0827-4650-8c81-7a24cf955f40",
    "source_timestamp": "1791025690734"
  }
  ```
- **What to say:** *"Notice this `datastream_metadata` column with its unique UUID. This is generated by Google Cloud Datastream CDC. It proves this row was streamed directly from PostgreSQL's transaction log without any manual export/import."*

---

## 7. Section 5: Live Analytics & Dashboards (BigQuery)

Now show the analytical data models built in BigQuery.

### Query 1: Source-Wise Compliance & DND Block Percentage
Run this in Cloud Shell:
```bash
bq query --use_legacy_sql=false \
  'SELECT source, total_ingested_contacts, dnd_blocked_count, approved_count, dnd_blocked_percentage FROM `wf006_analytics.v_source_compliance_metrics`;'
```

- **What to say:** *"This view aggregates leads by source channel (`CRM`, `CSV`, `WhatsApp`, `DCC`) and calculates the DND opt-out percentage. This directly feeds leadership dashboards in Looker Studio."*

---

### Query 2: Governance Decision Summary
Run this in Cloud Shell:
```bash
bq query --use_legacy_sql=false \
  'SELECT decision_date, decision, reason, total_contacts, total_events FROM `wf006_analytics.v_governance_decision_summary`;'
```

- **What to say:** *"This view summarizes all governance decisions across time for compliance audits."*

---

## 8. Presenter's Verbal Script: Exactly What to Say at Each Step

| Time | Screen / Tab | Script (Say Exactly This) |
| :---: | :--- | :--- |
| **0:00 - 0:45** | **Architecture Diagram** | *"Hare Krishna Prabhujis. Today I am demonstrating the completed WF-006 Proof of Concept. WF-006 is our Master Contact & Data Governance backbone. Its purpose is to guarantee clean identity, source attribution, and strict Do-Not-Disturb compliance before any outreach happens across WhatsApp or calling campaigns."* |
| **0:45 - 2:00** | **Swagger UI Tabs** | *"Here are our two microservices running live on Cloud Run. We decoupled validation from DND governance. In our Swagger UI, you can see how incoming contacts are validated against business schemas, and how our DND suppression registry blocks blacklisted phone numbers even if an upstream source sends them as clean."* |
| **2:00 - 3:15** | **Cloud Workflows** | *"Now let's see orchestration in action. Using Google Cloud Workflows, we pass an approved contact and see it persisted to Cloud SQL. When we pass a contact on the suppression list, the workflow branches automatically, excludes it from outreach, and writes an audit log."* |
| **3:15 - 4:15** | **Datastream & BigQuery** | *"Instead of batch ETL, Google Cloud Datastream reads the PostgreSQL Write-Ahead Log in real time. Here in BigQuery, you can see the synchronized records with their Datastream CDC metadata UUIDs."* |
| **4:15 - 5:00** | **Analytics & Wrap Up** | *"Finally, our BigQuery curated views generate source-wise compliance metrics and audit summaries ready for Looker dashboards. This completes the entire approved WF-006 architecture on live GCP infrastructure."* |

---

## 9. Answers to Tough Questions Leadership Might Ask

### Q1: *"Why do we have a separate DND Service instead of checking DND inside Cloud Run Validator?"*
> **Answer:**  
> *"Separation of concerns. Data validation checks schema and formatting (Is the phone E.164? Is owner specified?). DND Governance enforces organizational policy and legal compliance. By making DND an independent microservice, any downstream workflow (such as WF-002 Calling or WF-003 WhatsApp Campaigns) can query the exact same DND governance gate before sending messages."*

### Q2: *"Why use Datastream instead of writing directly to BigQuery from Cloud Run?"*
> **Answer:**  
> *"Dual-write anti-pattern. Writing to both PostgreSQL and BigQuery directly in the application code leads to data drift if one write fails. By using PostgreSQL as the ACID single source of truth and letting Datastream capture Write-Ahead Logs (WAL), we guarantee zero data loss and sub-minute synchronization without slowing down application transactions."*

### Q3: *"What is the cost of running this in Google Cloud?"*
> **Answer:**  
> *"All services are configured with cost guardrails: Cloud Run microservices scale to 0 instances when idle ($0 cost). BigQuery queries fall within the 1 TB monthly free tier. Cloud SQL uses the smallest micro-instance (~$0.015/hr). The entire POC operates well within Google Cloud's free tier and credits."*

### Q4: *"Can Datastream be paused when we are not running tests to save trial credits?"*
> **Answer:**  
> *"Yes! We can pause it anytime with:  
> `gcloud datastream streams update wf006-stream --location=us-central1 --state=PAUSED`  
> And resume it before any demo with:  
> `gcloud datastream streams update wf006-stream --location=us-central1 --state=RUNNING`"*
