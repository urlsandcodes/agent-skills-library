#!/usr/bin/env python3
"""Automated Flow & Edge-Case Test Gap Detector script.

Inspects .agents/architecture.md and test suites in target project,
identifying unasserted flow boundaries and edge cases.
"""

import json
import re
import sys
from pathlib import Path


def analyze_project(project_path: Path):
    arch_file = project_path / ".agents/architecture.md"
    if not arch_file.exists():
        print(f"Error: Architecture baseline not found at {arch_file}")
        sys.exit(1)

    with open(arch_file, "r", encoding="utf-8") as f:
        arch_content = f.read()

    # Find test files in project
    test_files = list(project_path.glob("**/test-*.js")) + list(
        project_path.glob("**/*.test.js")
    )
    test_files = [p for p in test_files if "node_modules" not in str(p) and ".next" not in str(p)]

    test_corpus = ""
    for tf in test_files:
        try:
            with open(tf, "r", encoding="utf-8") as f:
                test_corpus += f"\n--- {tf.name} ---\n" + f.read()
        except Exception:
            pass

    gaps = []

    # 1. Race Condition check on concurrent fulfillment
    if "Promise.all" not in test_corpus or "concurrent" not in test_corpus.lower():
        gaps.append({
            "id": "GAP-001",
            "flow_name": "Checkout & Payment Fulfillment",
            "category": "race-condition",
            "scenario": "Simultaneous browser verification and webhook delivery",
            "severity": "critical",
            "risk_description": "If browser redirect and Razorpay webhook hit server within milliseconds, race condition could result in double wallet crediting or conflicting order status.",
            "affected_components": ["checkout.controller", "payment.service", "wallet.model"],
            "current_coverage": "partial",
            "recommended_test_type": "integration",
            "recommended_test_case": "Spawn concurrent requests for checkout.verify and webhooks/payments using Promise.all on the same payment payload. Assert that wallet balance increments exactly once and order status remains completed."
        })

    # 2. Worker Expiry & Telegram Flood Wait
    if "FLOOD_WAIT" not in test_corpus and "429" not in test_corpus:
        gaps.append({
            "id": "GAP-002",
            "flow_name": "Telegram Outbox & Rate-Limiting",
            "category": "timeout-retry",
            "scenario": "Telegram API returns 429 FLOOD_WAIT error during outbox processing",
            "severity": "high",
            "risk_description": "If Telegram bot hits rate limits during a burst of channel operations, worker must back off and retry without marking task permanently failed.",
            "affected_components": ["telegramOutbox.service", "telegramOutbox.model"],
            "current_coverage": "none",
            "recommended_test_type": "unit",
            "recommended_test_case": "Mock Telegram API to reject with FLOOD_WAIT error. Run outbox worker and assert that task status remains PENDING or RETRY with exponential backoff delay."
        })

    # 3. Subscription Expiry & Automated Revocation
    if "runRevocationJob" not in test_corpus and "revocation.worker" not in test_corpus:
        gaps.append({
            "id": "GAP-003",
            "flow_name": "Subscription Lifecycle & Access Revocation",
            "category": "state-machine-skip",
            "scenario": "Subscription expiration sweeps and grace period boundary",
            "severity": "high",
            "risk_description": "Expiry and revocation workers run in background without explicit automated unit tests verifying member kick logic and grace period timing.",
            "affected_components": ["expiry.worker", "revocation.worker", "subscription.model"],
            "current_coverage": "none",
            "recommended_test_type": "integration",
            "recommended_test_case": "Create an expired subscription with accessStatus='granted'. Trigger runExpiryJob and runRevocationJob; assert subscription status transitions to 'expired' and an outbox KICK_MEMBER task is enqueued."
        })

    # 4. Partial Payment / Discrepancy Amount Mismatch
    if "discrepancy" not in test_corpus.lower() and "mismatch" not in test_corpus.lower():
        gaps.append({
            "id": "GAP-004",
            "flow_name": "Payment Reconciliation",
            "category": "partial-failure",
            "scenario": "Incoming webhook reports payment amount differing from order amount",
            "severity": "critical",
            "risk_description": "Price tampering or currency conversion discrepancies must log to PaymentDiscrepancy and halt automated entitlement grant.",
            "affected_components": ["payment.service", "paymentDiscrepancy.model"],
            "current_coverage": "none",
            "recommended_test_type": "integration",
            "recommended_test_case": "Send payment webhook with amount 50% less than order total. Assert payment is flagged in PaymentDiscrepancy and entitlement is NOT granted."
        })

    # 5. Unauthorized Download Link Access
    if "download" in arch_content.lower() and ("expired link" not in test_corpus.lower() and "unauthorized download" not in test_corpus.lower()):
        gaps.append({
            "id": "GAP-005",
            "flow_name": "Digital Products",
            "category": "unauthorized-mutation",
            "scenario": "Customer attempts downloading digital product without valid entitlement token",
            "severity": "medium",
            "risk_description": "Storefront endpoint must reject unauthenticated requests or expired presigned URLs with HTTP 401/403.",
            "affected_components": ["digitalProduct.controller", "storefront.service"],
            "current_coverage": "partial",
            "recommended_test_type": "integration",
            "recommended_test_case": "Request GET /api/store/digital-products/:id/download without authorization header. Assert HTTP 401 and zero S3 presigned URL generation."
        })

    return {
        "project": str(project_path),
        "test_files_scanned": [str(tf.name) for tf in test_files],
        "total_gaps": len(gaps),
        "gaps": gaps,
    }


def main():
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    results = analyze_project(target)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
