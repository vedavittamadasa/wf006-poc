# WF-006: Google Cloud Master Contact & Governance POC

## 1. Project Overview

This Proof of Concept (POC) implements the **WF-006 Architecture Flow** on Google Cloud Platform (GCP). It validates the end-to-end ingestion, validation, governance (Do Not Disturb - DND check), transactional persistence, real-time change data capture (CDC) synchronization, and analytical reporting for contact records.

---

## 2. Architecture & Data Flow

```text
Source Systems (CRM / CSV / WhatsApp / ERP)
      │
      ▼
API Gateway / Direct Pub/Sub Ingestion
      │
      ▼
Pub/Sub Topic (`wf006-contact-topic`)
      │
      ▼
Google Cloud Workflows (`wf006-orchestrator`)
      │
      ├──▶ Cloud Run: Contact Ingestion & Validation Service (`wf006-cloudrun`)
      │      • Validates required fields: Contact_ID, source, owner, format
      │
      ├──▶ Cloud Run: DND Service (`wf006-dnd-service`)
      │      • Verifies consent and DND status
      │      • Decision branch:
      │          - If DND = true: BLOCKS contact & logs decision in audit table
      │          - If DND = false: ALLOWS contact to continue
      │
      ▼
Cloud SQL PostgreSQL (`wf006-db` / tables: `contacts`, `contact_audit_log`)
      │
      ▼
Datastream (CDC Replication)
      │
      ▼
BigQuery Dataset (`wf006_analytics` / replicated raw tables)
      │
      ▼
Curated BigQuery Views / Reporting Queries
      │
      ▼
Looker / Dashboards / Downstream Workflows
```

---

## 3. Project Directory Structure

```text
wf006-poc/
├── README.md               # Architecture documentation, design specs, and POC guide
├── cloudrun/               # Contact Validation & Ingestion Microservice
│   ├── main.py             # FastAPI endpoints for contact validation & transformation
│   ├── requirements.txt     # Python dependencies (FastAPI, uvicorn, pydantic, psycopg2/sqlalchemy)
│   └── Dockerfile          # Container build spec for Cloud Run deployment
├── dnd-service/            # Dedicated Governance & DND Verification Microservice
│   ├── main.py             # FastAPI endpoint checking DND/consent registry
│   ├── requirements.txt     # Python dependencies (FastAPI, uvicorn, pydantic)
│   └── Dockerfile          # Container build spec for Cloud Run deployment
├── workflows/              # Orchestration Layer
│   └── wf006.yaml          # Google Cloud Workflows definition (step coordination, branching, error handling)
├── database/               # Transactional Master Data Layer
│   └── schema.sql          # Cloud SQL PostgreSQL DDL (`contacts`, `contact_audit_log`, indexes, triggers)
├── bigquery/               # Analytical Data Warehouse Layer
│   └── schema.sql          # BigQuery analytical schema, partitioning, and curated reporting views
├── pubsub/                 # Ingestion & Messaging Layer
│   └── sample-message.json # Example valid, invalid, and DND test contact payloads
└── scripts/                # Deployment & Verification Tooling
    └── deploy.sh           # Step-by-step gcloud CLI provisioning and verification script
```

---

## 4. Google Cloud Services Breakdown

| Service | Role in WF-006 | Why It Was Chosen |
| :--- | :--- | :--- |
| **Pub/Sub** | Asynchronous message broker | Decouples upstream source systems from ingestion logic, buffer bursts, guarantees at-least-once delivery. |
| **Google Cloud Workflows** | Central process orchestration | Serverless, declarative YAML workflow engine with native GCP IAM authentication, retries, and conditional branching. |
| **Cloud Run** | Microservice runtime | Fully managed, auto-scaling container execution environment with zero idle cost; hosts FastAPI services. |
| **DND Service (Cloud Run)** | Governance & Compliance gate | Independent policy service evaluating DND/opt-out status and recording auditable governance decisions. |
| **Cloud SQL (PostgreSQL)** | Transactional Master Database | ACID-compliant relational storage for operational master records and auditable history with primary key integrity. |
| **Datastream** | Change Data Capture (CDC) | Serverless, low-latency replication from PostgreSQL WAL logs straight into BigQuery without custom batch ETL pipelines. |
| **BigQuery** | Analytics Data Warehouse | Massively parallel SQL analytics engine for reporting, lifetime customer journey, conversion metrics, and downstream AI. |
| **Secret Manager + IAM** | Enterprise Security | Secure secret management (database credentials, tokens) combined with least-privilege IAM service accounts. |

---

## 5. Contact Data Model & Business Rules

### Core Contact Fields

| Field | Type | Description | Mandatory? |
| :--- | :--- | :--- | :--- |
| `Contact_ID` | `VARCHAR(64)` | Unique master contact identifier | **Yes** |
| `name` | `VARCHAR(255)` | Contact full name | No |
| `phone` | `VARCHAR(32)` | Phone / WhatsApp number (E.164 standard) | No (one of phone/email recommended) |
| `email` | `VARCHAR(255)` | Email address | No |
| `source` | `VARCHAR(64)` | Origin system (e.g. `CRM`, `CSV`, `WhatsApp`, `ERP`) | **Yes** |
| `owner` | `VARCHAR(128)` | Assigned owner / department ID | **Yes** |
| `consent_status` | `VARCHAR(32)` | Opt-in consent level (`GRANTED`, `REVOKED`, `PENDING`) | Yes |
| `dnd_status` | `BOOLEAN` | Do Not Disturb flag (`TRUE` = blocked, `FALSE` = active) | **Yes (checked by DND Service)** |
| `created_at` | `TIMESTAMP` | Record creation timestamp | Automatic |
| `updated_at` | `TIMESTAMP` | Record update timestamp | Automatic |

### Mandatory Business Rules

1. **Identity & Source Enforcement**: Every record must have `Contact_ID`, `source`, and `owner`. Any message missing these is routed to a dead-letter / failure log.
2. **Pre-Outreach DND Check**: The DND service must evaluate the record before any downstream outreach or operational persistence.
3. **Branching Logic**:
   - If `dnd_status == true` (or phone/email is registered in DND table): Contact is blocked from operational processing and an audit entry is recorded with reason `BLOCKED_DND`.
   - If `dnd_status == false`: Contact is written to Cloud SQL `contacts` table and audit entry records `APPROVED`.
4. **Audit Traceability**: Every decision must be logged in `contact_audit_log` with timestamp, status, and reason.

---

---

## 6. How to Run & Test Locally (Before Qwiklabs)

You can run and test the complete WF-006 pipeline locally on your machine without incurring any Google Cloud costs:

### One-Command Automated Run
From the `wf006-poc` directory, execute:
```bash
python scripts/run_local.py
```
Or in Windows PowerShell:
```powershell
.\scripts\start_local.ps1
```

This will automatically:
1. Start the **Contact Ingestion & Validator Service** on `http://127.0.0.1:8080`
2. Start the **DND Governance Service** on `http://127.0.0.1:8081`
3. Execute all 5 scenarios from `pubsub/sample-message.json`:
   - Valid contact passed & persisted in local database
   - DND-flagged contact blocked & audit logged
   - Suppression-registry contact blocked & audit logged
   - Missing-field contact rejected fast at validation gate
   - Pub/Sub base64 wrapped contact decoded and processed
4. Query and display the persisted Master Contacts and Audit Log records.

### Interactive API Exploration (Swagger UI)
To keep the microservices running so you can test them via interactive Swagger documentation:
```bash
python scripts/run_local.py --keep-running
```
Then open in your browser:
- **Contact Validator & Ingestion Service:** [http://127.0.0.1:8080/docs](http://127.0.0.1:8080/docs)
- **DND Governance Service:** [http://127.0.0.1:8081/docs](http://127.0.0.1:8081/docs)

---

## 7. Qwiklabs / GCP Resource Planning & Cost Guardrails

For a cost-effective POC in a Qwiklabs or Sandbox Google Cloud environment:
- **Cloud Run**: Configured with `min-instances=0`, `max-instances=2`, `memory=512Mi`, `cpu=1`. Zero cost when idle.
- **Cloud SQL**: Smallest tier `db-f1-micro` or `db-g1-small` with 10 GB SSD, single zone (no high-availability replica required for POC).
- **Pub/Sub**: Standard topic and pull/push subscription; minimal data volume incurs zero/cents cost.
- **Workflows**: Free tier allows up to 5,000 internal steps per month.
- **Datastream**: Pay per GB processed; negligible for test records.
- **BigQuery**: On-demand query pricing; free tier covers first 1 TB queries and 10 GB storage per month.
- **Secret Manager**: Free tier covers first 6 active secret versions.

---

## 8. Next Steps & Approval Workflow

This POC is implemented modularly. Each layer will be generated and validated in subsequent steps upon your approval:
- **Phase 1**: Project Structure & Architecture Specification (Completed)
- **Phase 2**: Local Testing & Verification (Completed)
- **Phase 3**: Prepare Google Cloud Project & Enable APIs
- **Phase 4**: Pub/Sub & Cloud SQL Provisioning
- **Phase 5**: Cloud Run & Workflows Deployment
- **Phase 6**: Datastream CDC & BigQuery Sync
- **Phase 7**: End-to-End Cloud Verification

