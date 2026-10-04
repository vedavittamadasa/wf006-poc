# WF-006 Proof of Concept: Live Demo Master Execution Script & Payloads

**Project Name:** WF-006 — CRM / DBMS / Data Governance Shared Data Backbone  
**GCP Project ID:** `project-225be79a-d654-49e1-950` | **Region:** `us-central1`  
**Live Swagger 1 (Ingestion & Integrations):** [https://wf006-cloudrun-662300223067.us-central1.run.app/docs](https://wf006-cloudrun-662300223067.us-central1.run.app/docs)  
**Live Swagger 2 (DND Governance Gate):** [https://wf006-dnd-service-662300223067.us-central1.run.app/docs](https://wf006-dnd-service-662300223067.us-central1.run.app/docs)  

---

## 🎯 How to Use This Script
For every step, follow this 3-part formula:
1. **Before Clicking:** Read the *What you are doing* and say the *Presenter's Script* to leadership.
2. **Clicking:** Paste the JSON payload and click **Execute**.
3. **After Execution:** Point to the specific fields in the response (UUID, Status, Message ID) to prove the architecture works.

---

## 📋 Table of Contents
1. [30-Second Architecture Introduction](#1-30-second-architecture-introduction)
2. [PART 1: Ingestion, Validation & Live Cloud Integrations (`wf006-cloudrun`)](#part-1-ingestion-validation--live-cloud-integrations)
   - [Step 1.1: Health & Database Backend Verification (`GET /health`)](#step-11-health--database-backend-verification-get-health)
   - [Step 1.2: API Gateway Security Contract (`GET /demo/api-gateway-contract`)](#step-12-api-gateway-security-contract-get-demoapi-gateway-contract)
   - [Step 1.3: Asynchronous Pub/Sub Ingestion (`POST /demo/publish-pubsub`)](#step-13-asynchronous-pubsub-ingestion-post-demopublish-pubsub)
   - [Step 1.4: Strict Schema Validation — Approved Devotee (`POST /validate`)](#step-14-strict-schema-validation--approved-devotee-post-validate)
   - [Step 1.5: Schema Rejection — Missing Source & Owner (`POST /validate`)](#step-15-schema-rejection--missing-source--owner-post-validate)
   - [Step 1.6: Schema Rejection — Unreachable Devotee (`POST /validate`)](#step-16-schema-rejection--unreachable-devotee-post-validate)
   - [Step 1.7: Cloud Workflows Live Execution — Approved Path (`POST /demo/trigger-workflow`)](#step-17-cloud-workflows-live-execution--approved-path-post-demotrigger-workflow)
   - [Step 1.8: Cloud Workflows Live Execution — Blocked Path (`POST /demo/trigger-workflow`)](#step-18-cloud-workflows-live-execution--blocked-path-post-demotrigger-workflow)
   - [Step 1.9: Transactional Database Inspection (`GET /contacts` & `GET /audit-logs`)](#step-19-transactional-database-inspection-get-contacts--get-audit-logs)
   - [Step 1.10: Datastream CDC Replication Status (`GET /demo/datastream-cdc-status`)](#step-110-datastream-cdc-replication-status-get-demodatastream-cdc-status)
   - [Step 1.11: BigQuery Replicated Lakehouse with CDC UUIDs (`GET /demo/bigquery-synced-contacts`)](#step-111-bigquery-replicated-lakehouse-with-cdc-uuids-get-demobigquery-synced-contacts)
   - [Step 1.12: Executive Compliance & DND Analytics View (`GET /demo/bigquery-compliance-metrics`)](#step-112-executive-compliance--dnd-analytics-view-get-demobigquery-compliance-metrics)
3. [PART 2: Dedicated DND Governance Service (`wf006-dnd-service`)](#part-2-dedicated-dnd-governance-service)
   - [Step 2.1: Suppression Registry Health (`GET /health`)](#step-21-suppression-registry-health-get-health)
   - [Step 2.2: Clean Devotee Cleared for Outreach (`POST /check-dnd`)](#step-22-clean-devotee-cleared-for-outreach-post-check-dnd)
   - [Step 2.3: Intercepted by Explicit DND Flag (`POST /check-dnd`)](#step-23-intercepted-by-explicit-dnd-flag-post-check-dnd)
   - [Step 2.4: Intercepted by Revoked Consent — DPDP Compliance (`POST /check-dnd`)](#step-24-intercepted-by-revoked-consent--dpdp-compliance-post-check-dnd)
   - [Step 2.5: Intercepted by Suppression Blacklist Registry (`POST /check-dnd`)](#step-25-intercepted-by-suppression-blacklist-registry-post-check-dnd)
4. [Answers to Leadership Questions (Data Lineage & Costs)](#4-answers-to-leadership-questions-data-lineage--costs)

---

## 1. 30-Second Architecture Introduction
**Say this to the audience at the start:**
> *"Hare Krishna Prabhujis and leaders. Today I am demonstrating the completed WF-006 Master Contact & Data Governance Backbone.  
> Its purpose is to solve our single biggest data challenge: before any outreach happens across WhatsApp campaigns or calling teams, ensuring every contact has verified identity, proper source attribution, and 100% strict Do-Not-Disturb legal compliance.  
> Everything you will see today is deployed live on Google Cloud Platform, running on Cloud Run, Cloud SQL PostgreSQL, Cloud Workflows, Datastream CDC, and BigQuery."*

---

# PART 1: Ingestion, Validation & Live Cloud Integrations
👉 **Open Swagger Tab 1:** [https://wf006-cloudrun-662300223067.us-central1.run.app/docs](https://wf006-cloudrun-662300223067.us-central1.run.app/docs)

---

### Step 1.1: Health & Database Backend Verification (`GET /health`)

* **What you are doing:** Checking service health and database connectivity.
* **Why you are doing it:** Proves the container is running live on Cloud Run and actively connected to Cloud SQL PostgreSQL.
* **🗣️ What to say before clicking:**
  > *"First, let us verify the health of our service and verify its active connection to our Cloud SQL PostgreSQL instance."*
* **Action:**
  1. Click `GET /health` ➔ **Try it out** ➔ **Execute**.
* **Payload:** *None*.
* **Expected Result (HTTP 200):**
  ```json
  {
    "service": "wf006-cloudrun",
    "status": "healthy",
    "database_backend": "PostgreSQL",
    "timestamp": "2026-10-05T00:30:00.000Z"
  }
  ```
* **🔍 Point out on screen:** `"database_backend": "PostgreSQL"` confirms live Cloud SQL connectivity.

---

### Step 1.2: API Gateway Security Contract (`GET /demo/api-gateway-contract`)

* **What you are doing:** Inspecting the API Gateway routing and rate limiting contract.
* **Why you are doing it:** Explains that Swagger is not just documentation; it is the official OpenAPI 3.0 specification uploaded to Google Cloud API Gateway to enforce TLS 1.3 encryption and 100 req/sec rate limits.
* **🗣️ What to say before clicking:**
  > *"Every endpoint exposed here is protected by Google Cloud API Gateway. Let's inspect the Gateway routing rules and security policies."*
* **Action:**
  1. Click `GET /demo/api-gateway-contract` ➔ **Try it out** ➔ **Execute**.
* **Payload:** *None*.
* **Expected Result (HTTP 200):**
  ```json
  {
    "api_gateway_name": "wf006-gateway",
    "gcp_service": "apigateway.googleapis.com",
    "security_policy": {
      "authentication": "Google OAuth2 / Service Account JWT",
      "tls_version": "TLS 1.3 Strict",
      "rate_limit": "100 requests/second per client_id"
    },
    "openapi_spec_url": "/openapi.json"
  }
  ```
* **🔍 Point out on screen:** Rate limiting (100 req/sec) and Google OAuth2 authentication.

---

### Step 1.3: Asynchronous Pub/Sub Ingestion (`POST /demo/publish-pubsub`)

* **What you are doing:** Publishing a devotee festival registration into Google Cloud Pub/Sub topic `wf006-contact-topic`.
* **Why you are doing it:** Shows the **entire automated event-driven pipeline**:
  1. The event enters the GCP Pub/Sub topic `wf006-contact-topic` in under 50ms.
  2. The message is buffered in `wf006-contact-sub` (where you can see it live when clicking **Pull** in GCP Console).
  3. Google Cloud Pub/Sub **automatically triggers the subscriber webhook** (`wf006-contact-auto-sub`).
  4. The workflow validates the schema, queries the DND Governance gate, and **persists to Cloud SQL PostgreSQL**.
  5. The PostgreSQL WAL commit triggers **Datastream CDC**, replicating the row to **BigQuery** in under 60 seconds!
* **🗣️ What to say before clicking:**
  > *"Watch this end-to-end automation. In one single click, an incoming WhatsApp lead enters Google Cloud Pub/Sub. From there, Pub/Sub automatically triggers our subscriber, executes the DND governance check, writes to Cloud SQL PostgreSQL, and Datastream streams it into BigQuery without any human intervention!"*
* **Action:**
  1. Click `POST /demo/publish-pubsub` ➔ **Try it out**.
  2. Paste this payload:
```json
{
  "Contact_ID": "CNT-FESTIVAL-2026-01",
  "name": "Gauranga Dasa",
  "phone": "+919876543210",
  "email": "gauranga.festival@example.org",
  "source": "WhatsApp",
  "owner": "seva-outreach-team",
  "consent_status": "GRANTED",
  "dnd_status": false
}
```
  3. Click **Execute**.
* **Expected Result (HTTP 200):**
  ```json
  {
    "status": "PUBLISHED",
    "topic": "projects/project-225be79a-d654-49e1-950/topics/wf006-contact-topic",
    "subscription": "projects/project-225be79a-d654-49e1-950/subscriptions/wf006-contact-sub",
    "message_id": "21325756034355362",
    "publish_time": "2026-10-05T00:31:00.000Z",
    "gcp_native_publish": true,
    "explanation": "Event accepted at the ingestion edge and queued in GCP Pub/Sub buffer without blocking transactional database."
  }
  ```
* **🔍 How to verify the automatic flow across the entire system:**
  1. **In Google Cloud Pub/Sub Console (`wf006-contact-sub`)**: Click **Messages ➔ Pull** ➔ See the message buffered in the queue!
  2. **In Swagger (`GET /contacts`)**: Click **Execute** ➔ See `CNT-FESTIVAL-2026-01` (`Gauranga Dasa`) automatically persisted in Cloud SQL PostgreSQL!
  3. **In Swagger (`GET /demo/bigquery-synced-contacts`)**: See the row synchronized in BigQuery with its Datastream CDC UUID!

---

### Step 1.4: Strict Schema Validation — Approved Devotee (`POST /validate`)

* **What you are doing:** Sending a complete, valid contact to the schema validator.
* **Why you are doing it:** Proves schema enforcement: verifies `Contact_ID`, `source`, `owner`, and formatting.
* **🗣️ What to say before clicking:**
  > *"Now we pass a complete devotee record through the Ingestion Validator to ensure it satisfies all data governance standards."*
* **Action:**
  1. Click `POST /validate` ➔ **Try it out**.
  2. Paste this payload:
```json
{
  "Contact_ID": "CNT-VALID-DEVOTEE-01",
  "name": "Radha Raman Das",
  "phone": "+919876543210",
  "email": "radha.raman@example.org",
  "source": "CRM",
  "owner": "seva-outreach-team",
  "consent_status": "GRANTED",
  "dnd_status": false
}
```
  3. Click **Execute**.
* **Expected Result (HTTP 200):**
  ```json
  {
    "status": "SUCCESS",
    "is_valid": true,
    "message": "Contact passed all schema and mandatory attribute validations."
  }
  ```
* **🔍 Point out on screen:** `"is_valid": true` and status `SUCCESS`.

---

### Step 1.5: Schema Rejection — Missing Source & Owner (`POST /validate`)

* **What you are doing:** Submitting a corrupt record missing mandatory provenance metadata (`source` and `owner`).
* **Why you are doing it:** Demonstrates that dirty or anonymous leads are stopped at the gate before entering the database.
* **🗣️ What to say before clicking:**
  > *"What happens if an external team uploads an anonymous contact missing `source` and `owner`? The system immediately rejects it with HTTP 422."*
* **Action:**
  1. In `POST /validate`, paste this payload:
```json
{
  "Contact_ID": "CNT-BAD-ANONYMOUS-01",
  "name": "Incomplete Donor Record",
  "phone": "+919811122233"
}
```
  2. Click **Execute**.
* **Expected Result (HTTP 422 Unprocessable Entity):**
  ```json
  {
    "detail": [
      { "type": "missing", "loc": ["body", "source"], "msg": "Field required" },
      { "type": "missing", "loc": ["body", "owner"], "msg": "Field required" }
    ]
  }
  ```
* **🔍 Point out on screen:** HTTP `422` error showing exactly which fields were missing.

---

### Step 1.6: Schema Rejection — Unreachable Devotee (`POST /validate`)

* **What you are doing:** Submitting a contact that has metadata but lacks *both* phone and email.
* **Why you are doing it:** Business rule enforcement: a contact record is useless if we have no channel to communicate with the devotee.
* **🗣️ What to say before clicking:**
  > *"If a record has an owner and source, but no phone and no email, our custom validator flags it as unreachable."*
* **Action:**
  1. In `POST /validate`, paste this payload:
```json
{
  "Contact_ID": "CNT-BAD-GHOST-01",
  "name": "Ghost Contact",
  "source": "CSV",
  "owner": "seva-outreach-team"
}
```
  2. Click **Execute**.
* **Expected Result (HTTP 422 Unprocessable Entity):**
  ```json
  {
    "detail": "Contact must include at least a phone number or an email address."
  }
  ```

---

### Step 1.7: Cloud Workflows Live Execution — Approved Path (`POST /demo/trigger-workflow`)

* **What you are doing:** Triggering the complete `wf006-orchestrator` state machine for an approved contact.
* **Why you are doing it:** Demonstrates Google Cloud Workflows coordination: Schema Validation ➔ DND Check ➔ Branch to Cloud SQL Persistence.
* **🗣️ What to say before clicking:**
  > *"Now let's see central orchestration in action. Cloud Workflows receives Sri Nityananda Dasa, validates the schema, queries the DND service, sees that consent is clean, and branches to persist the record into Cloud SQL."*
* **Action:**
  1. Click `POST /demo/trigger-workflow` ➔ **Try it out**.
  2. Paste this payload:
```json
{
  "contact": {
    "Contact_ID": "CNT-WF-APPROVED-01",
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
  3. Click **Execute**.
* **Expected Result (HTTP 200):**
  ```json
  {
    "workflow_name": "wf006-orchestrator",
    "execution_id": "wf-exec-7c89d12a",
    "status": "APPROVED",
    "branch_taken": "persist_master_contact",
    "contact_id": "CNT-WF-APPROVED-01",
    "persistence_status": "PERSISTED",
    "storage_backend": "Cloud SQL PostgreSQL",
    "message": "Contact validated, cleared DND governance, and stored in master database."
  }
  ```
* **🔍 Point out on screen:** `"branch_taken": "persist_master_contact"` and `"persistence_status": "PERSISTED"`.

---

### Step 1.8: Cloud Workflows Live Execution — Blocked Path (`POST /demo/trigger-workflow`)

* **What you are doing:** Triggering the workflow for a contact whose phone number `+919999999999` is on the DND suppression blacklist.
* **Why you are doing it:** Shows automatic governance branching: the contact is excluded from the master table and diverted to the audit log.
* **🗣️ What to say before clicking:**
  > *"Now watch what happens when an incoming lead contains a phone number on our DND blacklist. Even if the incoming payload claims `dnd_status: false`, Cloud Workflows intercepts it and branches away from the master table."*
* **Action:**
  1. In `POST /demo/trigger-workflow`, paste this payload:
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
  2. Click **Execute**.
* **Expected Result (HTTP 200):**
  ```json
  {
    "workflow_name": "wf006-orchestrator",
    "execution_id": "wf-exec-3b4e9f10",
    "status": "BLOCKED",
    "branch_taken": "audit_log_only",
    "contact_id": "CNT-WF-BLOCKED-01",
    "persistence_status": "EXCLUDED",
    "message": "Contact excluded from master outreach table; logged in immutable audit trail."
  }
  ```
* **🔍 Point out on screen:** `"branch_taken": "audit_log_only"` and `"persistence_status": "EXCLUDED"`.

---

### Step 1.9: Transactional Database Inspection (`GET /contacts` & `GET /audit-logs`)

* **What you are doing:** Querying the live records stored in Cloud SQL PostgreSQL.
* **Why you are doing it:** Proves the approved devotee exists in the master table, while the blocked devotee only exists in the audit log table.
* **🗣️ What to say before clicking:**
  > *"Let's inspect our Cloud SQL PostgreSQL database. Sri Nityananda Dasa is stored in our master contacts, while Kishore Kumar is safely isolated in the audit trail."*
* **Action:**
  1. Click `GET /contacts` ➔ **Try it out** ➔ **Execute** (Shows Sri Nityananda Dasa).
  2. Click `GET /audit-logs` ➔ **Try it out** ➔ **Execute** (Shows the BLOCKED decision for Kishore Kumar).

---

### Step 1.10: Datastream CDC Replication Status (`GET /demo/datastream-cdc-status`)

* **What you are doing:** Inspecting the real-time Google Cloud Datastream Change Data Capture (CDC) engine.
* **Why you are doing it:** Explains why our architecture has ZERO batch ETL jobs. Datastream reads PostgreSQL Write-Ahead Logs (WAL) continuously into BigQuery.
* **🗣️ What to say before clicking:**
  > *"Instead of writing dual-writes or running midnight batch jobs, Google Cloud Datastream captures every commit from PostgreSQL WAL logs via logical decoding. Let's verify the stream state."*
* **Action:**
  1. Click `GET /demo/datastream-cdc-status` ➔ **Try it out** ➔ **Execute**.
* **Payload:** *None*.
* **Expected Result (HTTP 200):**
  ```json
  {
    "datastream_name": "wf006-stream",
    "gcp_project": "project-225be79a-d654-49e1-950",
    "region": "us-central1",
    "state": "RUNNING",
    "cdc_architecture": {
      "source": {
        "engine": "Cloud SQL PostgreSQL 15",
        "replication_slot": "wf006_datastream_slot",
        "mechanism": "pgoutput logical decoding (WAL)"
      },
      "destination": {
        "engine": "Google BigQuery",
        "dataset": "public",
        "target_table": "public.contacts"
      }
    },
    "latency": "sub-minute (near real-time)"
  }
  ```
* **🔍 Point out on screen:** State is `RUNNING` and replication slot is `wf006_datastream_slot`.

---

### Step 1.11: BigQuery Replicated Lakehouse with CDC UUIDs (`GET /demo/bigquery-synced-contacts`)

* **What you are doing:** Inspecting the synchronized records inside Google BigQuery.
* **Why you are doing it:** Proves records were replicated by Datastream CDC through the presence of unique `datastream_metadata` UUIDs.
* **🗣️ What to say before clicking:**
  > *"Here are the synchronized records in Google BigQuery. Notice the Datastream CDC metadata UUID column. That UUID proves the record was streamed directly from PostgreSQL WAL logs."*
* **Action:**
  1. Click `GET /demo/bigquery-synced-contacts` ➔ **Try it out** ➔ **Execute**.
* **Payload:** *None*.
* **Expected Result (HTTP 200):**
  Shows contact records with the `datastream_metadata` object:
  ```json
  "datastream_metadata": {
    "uuid": "4f9d2a1b-3c4e-5f6a-7b8c-9d0e1f2a3b4c",
    "source_timestamp": "1791026000000",
    "change_type": "INSERT"
  }
  ```

---

### Step 1.12: Executive Compliance & DND Analytics View (`GET /demo/bigquery-compliance-metrics`)

* **What you are doing:** Querying analytical view `v_source_compliance_metrics`.
* **Why you are doing it:** Answers the leadership question: *"How do we know which lead source is reliable and compliant?"*
* **🗣️ What to say before clicking:**
  > *"Finally, here is our BigQuery analytical layer that powers Looker Studio dashboards. It computes the DND block percentage for every lead provider in real-time."*
* **Action:**
  1. Click `GET /demo/bigquery-compliance-metrics` ➔ **Try it out** ➔ **Execute**.
* **Payload:** *None*.
* **Expected Result (HTTP 200):**
  ```json
  {
    "view_name": "wf006_analytics.v_source_compliance_metrics",
    "dashboard_target": "Google Looker Studio / Executive Seva Dashboard",
    "metrics": [
      {
        "source": "CRM",
        "total_ingested_contacts": 4,
        "approved_count": 4,
        "dnd_blocked_count": 0,
        "dnd_blocked_percentage": "0.0%"
      },
      {
        "source": "WhatsApp",
        "total_ingested_contacts": 5,
        "approved_count": 3,
        "dnd_blocked_count": 2,
        "dnd_blocked_percentage": "40.0%"
      }
    ]
  }
  ```
* **🔍 Point out on screen:** CRM has `0.0%` DND block rate, while WhatsApp has `40.0%`, helping leadership identify risky lead channels immediately.

---
---

# PART 2: Dedicated DND Governance Service
👉 **Open Swagger Tab 2:** [https://wf006-dnd-service-662300223067.us-central1.run.app/docs](https://wf006-dnd-service-662300223067.us-central1.run.app/docs)

* **🗣️ What to say to Leadership:**
  > *"Notice that DND Governance is deployed as a completely independent microservice. It is an impartial compliance gatekeeper that cannot be bypassed by any outreach campaign across WhatsApp or voice calling."*

---

### Step 2.1: Suppression Registry Health (`GET /health`)

* **What you are doing:** Checking the suppression blacklist registry count.
* **Action:** Click `GET /health` ➔ **Try it out** ➔ **Execute**.
* **Expected Result (HTTP 200):** Shows `suppression_registry_count: 7`.

---

### Step 2.2: Clean Devotee Cleared for Outreach (`POST /check-dnd`)

* **What you are doing:** Verifying a devotee with active consent.
* **🗣️ What to say:** *"A clean devotee with active consent returns `ALLOW`."*
* **Action:**
  1. Click `POST /check-dnd` ➔ **Try it out**.
  2. Paste this payload:
```json
{
  "Contact_ID": "CNT-CLEAN-DEVOTEE-01",
  "phone": "+919876500001",
  "email": "clean.devotee@example.org",
  "consent_status": "GRANTED",
  "dnd_status": false
}
```
  3. Click **Execute**.
* **Expected Result (HTTP 200):**
  ```json
  {
    "Contact_ID": "CNT-CLEAN-DEVOTEE-01",
    "is_dnd": false,
    "action": "ALLOW",
    "reason": "Contact is verified and not on any suppression lists"
  }
  ```

---

### Step 2.3: Intercepted by Explicit DND Flag (`POST /check-dnd`)

* **What you are doing:** Testing a payload where `dnd_status: true`.
* **🗣️ What to say:** *"If an incoming contact has an explicit DND flag, it is immediately blocked."*
* **Payload:**
```json
{
  "Contact_ID": "CNT-EXPLICIT-DND-01",
  "phone": "+919811122233",
  "email": "optout@example.com",
  "consent_status": "PENDING",
  "dnd_status": true
}
```
* **Expected Result (HTTP 200):** `"action": "BLOCK"`, `"reason": "Payload contains explicit dnd_status=true"`.

---

### Step 2.4: Intercepted by Revoked Consent — DPDP Compliance (`POST /check-dnd`)

* **What you are doing:** Testing a devotee whose `consent_status: "REVOKED"`.
* **🗣️ What to say:** *"Under India's Digital Personal Data Protection (DPDP) Act, when a devotee revokes consent, outreach is illegal. Our governance gate intercepts this immediately."*
* **Payload:**
```json
{
  "Contact_ID": "CNT-REVOKED-CONSENT-01",
  "phone": "+919822233344",
  "email": "revoked.donor@example.com",
  "consent_status": "REVOKED",
  "dnd_status": false
}
```
* **Expected Result (HTTP 200):** `"action": "BLOCK"`, `"reason": "Consent status is REVOKED by user"`.

---

### Step 2.5: Intercepted by Suppression Blacklist Registry (`POST /check-dnd`)

* **What you are doing:** A contact claims `dnd_status: false`, but their phone `+919999999999` is on the central blacklist.
* **🗣️ What to say:** *"Here is the most powerful scenario: an external CRM marks this lead as clean (`dnd_status: false`), but our central registry catches the blacklisted phone number `+919999999999` and blocks it."*
* **Payload:**
```json
{
  "Contact_ID": "CNT-SUPPRESSED-PHONE-01",
  "phone": "+919999999999",
  "email": "tricky.lead@example.com",
  "consent_status": "GRANTED",
  "dnd_status": false
}
```
* **Expected Result (HTTP 200):** `"action": "BLOCK"`, `"reason": "Phone number +919999999999 is listed in the DND suppression registry"`.

---

## 4. Answers to Leadership Questions (Data Lineage & Costs)

### Q1: *"From where does the data in `/demo/bigquery-compliance-metrics` come from?"*
> **Answer:**  
> *"Every incoming contact has a mandatory `source` tag (`CRM`, `WhatsApp`, `CSV`, `DCC`).  
> When the DND service evaluates the contact, it logs whether the record was approved or blocked.  
> Google Cloud Datastream streams these records continuously from PostgreSQL into BigQuery.  
> In BigQuery, the view `v_source_compliance_metrics` executes an analytical `GROUP BY source` query that calculates total leads, approved counts, blocked counts, and the compliance percentage in real time."*

### Q2: *"Why is DND a separate service instead of just a function inside Cloud Run?"*
> **Answer:**  
> *"Separation of concerns. Data validation checks formatting. DND Governance enforces organizational policy. By keeping DND as an independent service, any future workflow (such as WF-002 Calling or WF-003 WhatsApp Campaigns) queries the exact same DND governance gate before sending any message."*

### Q3: *"What is the monthly cost of this infrastructure?"*
> **Answer:**  
> *"All services are built with strict serverless cost guardrails. Cloud Run scales to zero ($0 when idle). Cloud SQL runs on the smallest micro instance (~$0.015/hour). BigQuery falls within the 1 TB monthly free tier. The entire POC operates well within Google Cloud's free credits."*
