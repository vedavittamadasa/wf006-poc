#!/usr/bin/env python
"""
WF-006 Local End-to-End Orchestrator and Test Runner
=====================================================
Simulates the Google Cloud Workflows orchestration locally:
  Pub/Sub Event -> Ingestion & Validation Service (8080) -> DND Governance Service (8081) -> Database (SQLite/Cloud SQL)

Usage:
  python scripts/run_local.py
  python scripts/run_local.py --keep-running
"""

import os
import sys
import time
import json
import base64
import socket
import argparse
import subprocess
import requests
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
CLOUDRUN_DIR = BASE_DIR / "cloudrun"
DND_DIR = BASE_DIR / "dnd-service"
SAMPLE_MSG_PATH = BASE_DIR / "pubsub" / "sample-message.json"

VALIDATOR_PORT = 8080
DND_PORT = 8081
VALIDATOR_URL = f"http://127.0.0.1:{VALIDATOR_PORT}"
DND_URL = f"http://127.0.0.1:{DND_PORT}"


def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) == 0


def start_service(name: str, cwd: Path, port: int):
    if is_port_in_use(port):
        print(f"[*] {name} already running on port {port}")
        return None
    print(f"[>] Starting {name} on port {port}...")
    log_name = f"local_service_{port}.log"
    log_file = open(BASE_DIR / log_name, "w", encoding="utf-8")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "main:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=cwd,
        stdout=log_file,
        stderr=subprocess.STDOUT
    )
    return proc


def wait_for_health(url: str, name: str, timeout: int = 15):
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            res = requests.get(f"{url}/health", timeout=2)
            if res.status_code == 200:
                print(f"[+] {name} is healthy: {res.json()}")
                return True
        except requests.exceptions.RequestException:
            pass
        time.sleep(0.5)
    raise RuntimeError(f"Timeout waiting for {name} at {url}/health")



def run_orchestrator_step(test_id: str, case_data: dict):
    print("\n" + "=" * 70)
    print(f"TEST SCENARIO: {test_id}")
    print(f"Description: {case_data.get('description')}")
    print("=" * 70)

    # 1. Simulate Pub/Sub reception and unwrapping
    raw_payload = case_data.get("payload")
    if not raw_payload and "message" in case_data:
        # Pub/Sub wrapped message with base64 data
        b64_data = case_data["message"]["data"]
        raw_payload = json.loads(base64.b64decode(b64_data).decode("utf-8"))
        print(f"[*] Pub/Sub message decoded: Contact_ID={raw_payload.get('Contact_ID')}")

    contact_id = raw_payload.get("Contact_ID", "UNKNOWN")
    print(f"[*] Input Contact: {json.dumps(raw_payload, indent=2)}")

    # 2. Step 1: Validation
    print("\n[Step 1] Calling Contact Validation Service (/validate)...")
    try:
        val_res = requests.post(f"{VALIDATOR_URL}/validate", json=raw_payload, timeout=5)
    except Exception as exc:
        print(f"[-] Validation request failed: {exc}")
        return

    if val_res.status_code != 200:
        print(f"[-] VALIDATION FAILED (HTTP {val_res.status_code}): {val_res.text}")
        print(f"[!] Contact {contact_id} halted at validation gate as expected by WF-006 rules.")
        return

    validated_contact = val_res.json()["contact"]
    print(f"[+] VALIDATION PASSED: {val_res.json().get('message')}")

    # 3. Step 2: DND Governance Gate
    print("\n[Step 2] Calling Dedicated DND Governance Service (/check-dnd)...")
    dnd_payload = {
        "Contact_ID": validated_contact.get("Contact_ID"),
        "phone": validated_contact.get("phone"),
        "email": validated_contact.get("email"),
        "consent_status": validated_contact.get("consent_status", "PENDING"),
        "dnd_status": validated_contact.get("dnd_status", False)
    }
    dnd_res = requests.post(f"{DND_URL}/check-dnd", json=dnd_payload, timeout=5)
    dnd_result = dnd_res.json()
    print(f"[*] DND Service Result: Action={dnd_result.get('action')}, is_dnd={dnd_result.get('is_dnd')}")
    print(f"    Reason: {dnd_result.get('reason')}")

    # 4. Step 3: Branching Logic
    if dnd_result.get("action") == "BLOCK" or dnd_result.get("is_dnd") is True:
        print("\n[Step 3: Branch A] CONTACT BLOCKED BY DND GOVERNANCE")
        print("    -> Routing to /audit-log (Excluded from operational master outreach)")
        audit_payload = {
            "contact_id": contact_id,
            "decision": "BLOCKED",
            "reason": dnd_result.get("reason"),
            "details": {
                "source": validated_contact.get("source"),
                "owner": validated_contact.get("owner"),
                "phone": validated_contact.get("phone"),
                "email": validated_contact.get("email")
            }
        }
        audit_res = requests.post(f"{VALIDATOR_URL}/audit-log", json=audit_payload, timeout=5)
        print(f"[+] Audit Log Recorded: {audit_res.json()}")
    else:
        print("\n[Step 3: Branch B] CONTACT APPROVED")
        print("    -> Persisting to Master Database (/persist)")
        persist_res = requests.post(f"{VALIDATOR_URL}/persist", json=validated_contact, timeout=5)
        print(f"[+] Persistence Outcome: {persist_res.json()}")


def main():
    parser = argparse.ArgumentParser(description="WF-006 Local Orchestrator")
    parser.add_argument("--keep-running", action="store_true", help="Keep services alive after tests finish")
    args = parser.parse_args()

    procs = []
    try:
        # Start microservices
        p1 = start_service("Cloud Run Ingestion & Validator Service", CLOUDRUN_DIR, VALIDATOR_PORT)
        if p1:
            procs.append(p1)
        p2 = start_service("Cloud Run DND Governance Service", DND_DIR, DND_PORT)
        if p2:
            procs.append(p2)

        # Health checks
        print("\n[*] Waiting for microservices to become ready...")
        wait_for_health(VALIDATOR_URL, "Validator Service")
        wait_for_health(DND_URL, "DND Service")

        # Load test cases
        with open(SAMPLE_MSG_PATH, "r", encoding="utf-8") as f:
            test_suite = json.load(f)["test_cases"]

        print(f"\n[*] Loaded {len(test_suite)} test scenarios from sample-message.json")
        for test_id, case_data in test_suite.items():
            run_orchestrator_step(test_id, case_data)

        # Query Database
        print("\n" + "=" * 70)
        print("FINAL DATABASE VERIFICATION")
        print("=" * 70)
        contacts = requests.get(f"{VALIDATOR_URL}/contacts").json()
        print(f"\n[+] Master Contacts Persisted ({len(contacts)} records):")
        for c in contacts:
            print(f"    - ID: {c.get('contact_id')} | Name: {c.get('name')} | Source: {c.get('source')} | Owner: {c.get('owner')} | DND: {c.get('dnd_status')}")

        audit_logs = requests.get(f"{VALIDATOR_URL}/audit-logs").json()
        print(f"\n[+] Contact Audit Logs Recorded ({len(audit_logs)} records):")
        for a in audit_logs:
            print(f"    - ID: {a.get('contact_id')} | Decision: {a.get('decision')} | Reason: {a.get('reason')}")

        print("\n" + "=" * 70)
        print("[SUCCESS] All local test scenarios completed successfully!")
        print(f"Interactive API Docs available at:")
        print(f"  • Contact Validator: {VALIDATOR_URL}/docs")
        print(f"  • DND Service:       {DND_URL}/docs")
        print("=" * 70)

        if args.keep_running:
            print("\n[*] Microservices are running in background. Press Ctrl+C to terminate.")
            while True:
                time.sleep(1)

    except KeyboardInterrupt:
        print("\n[*] Terminating services...")
    finally:
        for p in procs:
            p.terminate()
            p.wait()


if __name__ == "__main__":
    main()
