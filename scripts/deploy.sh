#!/usr/bin/env bash
# =============================================================================
# WF-006 Google Cloud POC - Deployment & Provisioning Script
# =============================================================================
# CAUTION:
# - Run this script step-by-step in your Qwiklabs / GCP Cloud Shell environment.
# - Do NOT run blindly without verifying your GCP PROJECT_ID.
# - All services are configured with minimal tiers to prevent unnecessary costs.
# =============================================================================

set -euo pipefail

# -----------------------------------------------------------------------------
# Configuration Variables (Review before executing)
# -----------------------------------------------------------------------------
export PROJECT_ID=$(gcloud config get-value project)
export REGION="us-central1"
export ZONE="us-central1-a"
export SERVICE_ACCOUNT_NAME="wf006-sa"
export SERVICE_ACCOUNT="${SERVICE_ACCOUNT_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

export REPO_NAME="wf006-repo"
export PUBSUB_TOPIC="wf006-contact-topic"
export PUBSUB_SUB="wf006-contact-sub"

export CLOUDRUN_VALIDATOR="wf006-cloudrun"
export CLOUDRUN_DND="wf006-dnd-service"
export WORKFLOW_NAME="wf006-orchestrator"

export DB_INSTANCE="wf006-postgres"
export DB_NAME="wf006_db"
export DB_USER="postgres"
export BQ_DATASET="wf006_analytics"

echo "=========================================================="
echo " Starting WF-006 Google Cloud Deployment"
echo " Project ID : ${PROJECT_ID}"
echo " Region     : ${REGION}"
echo " Service Acc: ${SERVICE_ACCOUNT}"
echo "=========================================================="

# -----------------------------------------------------------------------------
# Step 1: Enable Necessary Google Cloud APIs
# -----------------------------------------------------------------------------
echo "--> [1/8] Enabling required GCP service APIs..."
gcloud services enable \
    run.googleapis.com \
    workflows.googleapis.com \
    workflowexecutions.googleapis.com \
    pubsub.googleapis.com \
    sqladmin.googleapis.com \
    datastream.googleapis.com \
    bigquery.googleapis.com \
    secretmanager.googleapis.com \
    artifactregistry.googleapis.com \
    cloudbuild.googleapis.com \
    iam.googleapis.com \
    --project="${PROJECT_ID}"

# -----------------------------------------------------------------------------
# Step 2: Create Service Account and Assign Least-Privilege IAM Roles
# -----------------------------------------------------------------------------
echo "--> [2/8] Creating service account and binding IAM roles..."
if ! gcloud iam service-accounts describe "${SERVICE_ACCOUNT}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
    gcloud iam service-accounts create "${SERVICE_ACCOUNT_NAME}" \
        --display-name="WF-006 Orchestrator and Cloud Run Service Account" \
        --project="${PROJECT_ID}"
fi

# Assign roles: Workflows Invoker, Cloud Run Invoker, Cloud SQL Client, Logging
for ROLE in \
    roles/run.invoker \
    roles/workflows.invoker \
    roles/cloudsql.client \
    roles/secretmanager.secretAccessor \
    roles/logging.logWriter; do
    gcloud projects add-iam-policy-binding "${PROJECT_ID}" \
        --member="serviceAccount:${SERVICE_ACCOUNT}" \
        --role="${ROLE}" \
        --condition=None --quiet >/dev/null
done

# -----------------------------------------------------------------------------
# Step 3: Create Artifact Registry for Docker Images
# -----------------------------------------------------------------------------
echo "--> [3/8] Setting up Artifact Registry repository..."
if ! gcloud artifacts repositories describe "${REPO_NAME}" --location="${REGION}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
    gcloud artifacts repositories create "${REPO_NAME}" \
        --repository-format=docker \
        --location="${REGION}" \
        --description="Docker repository for WF-006 microservices" \
        --project="${PROJECT_ID}"
fi

# -----------------------------------------------------------------------------
# Step 4: Build and Deploy Cloud Run Microservices
# -----------------------------------------------------------------------------
echo "--> [4/8] Building and deploying Cloud Run services..."

# Build & Deploy Validator Service
echo "    Deploying ${CLOUDRUN_VALIDATOR}..."
gcloud builds submit ../cloudrun \
    --tag="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${CLOUDRUN_VALIDATOR}:v1" \
    --project="${PROJECT_ID}"

gcloud run deploy "${CLOUDRUN_VALIDATOR}" \
    --image="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${CLOUDRUN_VALIDATOR}:v1" \
    --region="${REGION}" \
    --service-account="${SERVICE_ACCOUNT}" \
    --min-instances=0 \
    --max-instances=2 \
    --memory=512Mi \
    --cpu=1 \
    --allow-unauthenticated \
    --project="${PROJECT_ID}"

VALIDATOR_URL=$(gcloud run services describe "${CLOUDRUN_VALIDATOR}" --region="${REGION}" --format='value(status.url)' --project="${PROJECT_ID}")

# Build & Deploy DND Service
echo "    Deploying ${CLOUDRUN_DND}..."
gcloud builds submit ../dnd-service \
    --tag="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${CLOUDRUN_DND}:v1" \
    --project="${PROJECT_ID}"

gcloud run deploy "${CLOUDRUN_DND}" \
    --image="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO_NAME}/${CLOUDRUN_DND}:v1" \
    --region="${REGION}" \
    --service-account="${SERVICE_ACCOUNT}" \
    --min-instances=0 \
    --max-instances=2 \
    --memory=512Mi \
    --cpu=1 \
    --allow-unauthenticated \
    --project="${PROJECT_ID}"

DND_URL=$(gcloud run services describe "${CLOUDRUN_DND}" --region="${REGION}" --format='value(status.url)' --project="${PROJECT_ID}")

echo "    Validator URL : ${VALIDATOR_URL}"
echo "    DND URL       : ${DND_URL}"

# -----------------------------------------------------------------------------
# Step 5: Deploy Google Cloud Workflows
# -----------------------------------------------------------------------------
echo "--> [5/8] Deploying Google Cloud Workflow orchestrator..."
gcloud workflows deploy "${WORKFLOW_NAME}" \
    --source="../workflows/wf006.yaml" \
    --location="${REGION}" \
    --service-account="${SERVICE_ACCOUNT}" \
    --project="${PROJECT_ID}"

# -----------------------------------------------------------------------------
# Step 6: Create Pub/Sub Topic and Subscription
# -----------------------------------------------------------------------------
echo "--> [6/8] Configuring Pub/Sub..."
if ! gcloud pubsub topics describe "${PUBSUB_TOPIC}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
    gcloud pubsub topics create "${PUBSUB_TOPIC}" --project="${PROJECT_ID}"
fi

if ! gcloud pubsub subscriptions describe "${PUBSUB_SUB}" --project="${PROJECT_ID}" >/dev/null 2>&1; then
    gcloud pubsub subscriptions create "${PUBSUB_SUB}" \
        --topic="${PUBSUB_TOPIC}" \
        --project="${PROJECT_ID}"
fi

# -----------------------------------------------------------------------------
# Step 7: Create BigQuery Dataset and Tables
# -----------------------------------------------------------------------------
echo "--> [7/8] Provisioning BigQuery Dataset and Schemas..."
bq --location=US mk -d --description "WF-006 Analytics dataset" "${PROJECT_ID}:${BQ_DATASET}" || true
bq query --use_legacy_sql=false < ../bigquery/schema.sql

# -----------------------------------------------------------------------------
# Step 8: Cloud SQL Provisioning (Prompts before creating expensive resource)
# -----------------------------------------------------------------------------
echo "--> [8/8] Cloud SQL PostgreSQL..."
echo "NOTE: Cloud SQL incurs hourly cost ($0.015/hr for db-f1-micro)."
read -p "Do you want to provision Cloud SQL now? (y/N): " CREATE_SQL
if [[ "$CREATE_SQL" =~ ^[Yy]$ ]]; then
    gcloud sql instances create "${DB_INSTANCE}" \
        --database-version=POSTGRES_15 \
        --tier=db-f1-micro \
        --region="${REGION}" \
        --storage-size=10GB \
        --storage-type=SSD \
        --database-flags=cloudsql.logical_decoding=on \
        --project="${PROJECT_ID}"
    
    gcloud sql databases create "${DB_NAME}" --instance="${DB_INSTANCE}" --project="${PROJECT_ID}"
    echo "Cloud SQL instance ${DB_INSTANCE} created successfully."
else
    echo "Skipped Cloud SQL provisioning. Microservices will operate in simulation mode."
fi

echo "=========================================================="
echo " WF-006 Deployment & Setup Completed!"
echo " Test Workflow with sample payload:"
echo " gcloud workflows run ${WORKFLOW_NAME} --location=${REGION} --data='{\"validator_url\":\"${VALIDATOR_URL}\",\"dnd_url\":\"${DND_URL}\",\"contact\":{\"Contact_ID\":\"CNT-001\",\"name\":\"Test User\",\"phone\":\"+919876543210\",\"source\":\"CRM\",\"owner\":\"test-team\",\"consent_status\":\"GRANTED\",\"dnd_status\":false}}'"
echo "=========================================================="
