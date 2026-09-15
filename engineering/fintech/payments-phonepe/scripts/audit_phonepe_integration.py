#!/usr/bin/env python3
"""Audit a codebase for secure, compliant PhonePe Payment Gateway (V2) integration."""

from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any, Dict, List


def audit_project(target_dir: Path) -> Dict[str, Any]:
    findings: List[Dict[str, Any]] = []

    # Pillar 1: V2 OAuth Authentication (25 pts)
    auth_score = 0.0
    has_oauth_token = False
    has_deprecated_salt_key = False
    
    # Pillar 2: Order Creation Payload & Idempotency (25 pts)
    order_score = 0.0
    has_v2_pay = False
    has_order_idempotency = False
    has_paise_conversion = False
    
    # Pillar 3: Webhook Signature Verification (25 pts)
    webhook_score = 0.0
    has_webhook_signature_check = False
    has_timing_safe_equal = False
    
    # Pillar 4: Server Status Reconciliation (25 pts)
    status_score = 0.0
    has_server_status_api = False
    relies_solely_on_client_redirect = False

    valid_exts = {".ts", ".tsx", ".js", ".jsx", ".py", ".java", ".kt", ".go", ".php"}

    for file_path in target_dir.rglob("*"):
        if not file_path.is_file() or file_path.suffix not in valid_exts:
            continue
        if any(part in file_path.parts for part in [".git", "node_modules", "dist", "build", ".venv"]):
            continue

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        content_lower = content.lower()

        # Check Auth
        if "oauth/token" in content_lower or ("client_id" in content_lower and "client_secret" in content_lower and "client_version" in content_lower):
            has_oauth_token = True

        if "salt_key" in content_lower or "saltkey" in content_lower or "x-verify" in content_lower:
            has_deprecated_salt_key = True

        # Check Order Creation
        if "/v2/pay" in content_lower or "pg_checkout" in content_lower:
            has_v2_pay = True

        if "merchantorderid" in content_lower or "merchant_order_id" in content_lower:
            has_order_idempotency = True

        if "* 100" in content or "amountinpaise" in content_lower or "paise" in content_lower:
            has_paise_conversion = True

        # Check Webhook Signature
        if ("hmac" in content_lower and "sha256" in content_lower) or "signature" in content_lower and "webhook" in content_lower:
            has_webhook_signature_check = True

        if "timingsafeequal" in content_lower or "constant_time_compare" in content_lower or "hmac.compare_digest" in content_lower:
            has_timing_safe_equal = True

        # Check Status API
        if "/v2/order/" in content_lower and "status" in content_lower:
            has_server_status_api = True

        if "redirecturl" in content_lower and "order" in content_lower and not has_server_status_api:
            # potential risk if they complete orders upon redirect landing
            if "status === 'success'" in content_lower or "status == 'success'" in content_lower:
                relies_solely_on_client_redirect = True

    # Compute Pillar 1 (OAuth Auth)
    if has_deprecated_salt_key:
        findings.append({
            "id": "PHONEPE-AUTH-01",
            "pillar": "v2_oauth_auth",
            "status": "fail",
            "title": "Deprecated V1 Salt Key / X-VERIFY In Use",
            "details": "Legacy Salt Keys detected. PhonePe has deprecated V1 credentials in favor of V2 OAuth tokens.",
            "remediation": "Migrate to Client ID, Client Secret, and Client Version with OAuth token exchange."
        })
    elif has_oauth_token:
        auth_score = 25.0
        findings.append({
            "id": "PHONEPE-AUTH-01",
            "pillar": "v2_oauth_auth",
            "status": "pass",
            "title": "Compliant PhonePe V2 OAuth Credentials",
            "details": "Uses client_id, client_secret, and client_version with OAuth /v1/oauth/token.",
            "remediation": "Ensure client secret is secured in environment variables or KMS."
        })
    else:
        findings.append({
            "id": "PHONEPE-AUTH-01",
            "pillar": "v2_oauth_auth",
            "status": "fail",
            "title": "Missing PhonePe V2 OAuth Implementation",
            "details": "No standard PhonePe V2 OAuth token flow detected.",
            "remediation": "Implement OAuth token generation endpoint using client credentials."
        })

    # Compute Pillar 2 (Order Creation)
    if has_v2_pay:
        order_score += 15.0
    if has_order_idempotency:
        order_score += 5.0
    if has_paise_conversion:
        order_score += 5.0

    if order_score >= 20.0:
        findings.append({
            "id": "PHONEPE-ORD-01",
            "pillar": "order_creation_payload",
            "status": "pass",
            "title": "Standard V2 Pay Order Creation",
            "details": "Order payload adheres to PhonePe V2 specifications with idempotent merchantOrderId.",
            "remediation": "Maintain strict integer paise units for all transaction amounts."
        })
    else:
        findings.append({
            "id": "PHONEPE-ORD-01",
            "pillar": "order_creation_payload",
            "status": "fail",
            "title": "Non-Standard Order Creation",
            "details": "Missing V2 /v2/pay endpoint invocation or merchant order idempotency key.",
            "remediation": "Invoke /v2/pay with integer paise and unique merchantOrderId."
        })

    # Compute Pillar 3 (Webhook Signature)
    if has_webhook_signature_check:
        webhook_score += 15.0
        if has_timing_safe_equal:
            webhook_score += 10.0
            findings.append({
                "id": "PHONEPE-WH-01",
                "pillar": "webhook_signature_verification",
                "status": "pass",
                "title": "Secure Constant-Time Webhook HMAC Verification",
                "details": "Webhook signatures verified via HMAC-SHA256 with timing-attack prevention.",
                "remediation": "Keep webhook callback endpoint idempotent."
            })
        else:
            findings.append({
                "id": "PHONEPE-WH-01",
                "pillar": "webhook_signature_verification",
                "status": "warn",
                "title": "Webhook Signature Check Lacks Constant-Time Comparison",
                "details": "Signatures checked without timingSafeEqual, leaving surface for timing attacks.",
                "remediation": "Use crypto.timingSafeEqual or hmac.compare_digest for signature checks."
            })
    else:
        findings.append({
            "id": "PHONEPE-WH-01",
            "pillar": "webhook_signature_verification",
            "status": "fail",
            "title": "Missing Webhook HMAC Signature Verification",
            "details": "Webhooks processed without verifying PhonePe cryptographic authenticity.",
            "remediation": "Verify X-Signature header using HMAC-SHA256 with clientSecret before processing."
        })

    # Compute Pillar 4 (Reconciliation)
    if has_server_status_api:
        status_score = 25.0
        findings.append({
            "id": "PHONEPE-REC-01",
            "pillar": "server_status_reconciliation",
            "status": "pass",
            "title": "Authoritative Order Status API Reconciliation",
            "details": "Server invokes /v2/order/{merchantOrderId}/status to verify true payment state.",
            "remediation": "Poll or schedule periodic reconciliation for pending transactions."
        })
    else:
        findings.append({
            "id": "PHONEPE-REC-01",
            "pillar": "server_status_reconciliation",
            "status": "fail",
            "title": "Missing Authoritative Server Status Check",
            "details": "System does not verify payment state via PhonePe /v2/order status API.",
            "remediation": "Always verify payment state on backend before fulfilling orders or provisioning credits."
        })

    overall_score = round(auth_score + order_score + webhook_score + status_score, 1)

    recommendations = [
        "Use PhonePe V2 OAuth authentication with Client ID and Client Secret (avoid deprecated V1 Salt Keys).",
        "Generate unique, idempotent merchantOrderId values for all transaction requests.",
        "Pass amounts in integer paise (1 INR = 100 paise) to prevent floating point conversion bugs.",
        "Verify server-to-server webhook callbacks with HMAC-SHA256 in constant time (timingSafeEqual).",
        "Never fulfill orders on browser redirect; always query the authoritative /v2/order status API."
    ]

    return {
        "target": str(target_dir),
        "audited_at": datetime.now(timezone.utc).isoformat(),
        "overall_score": overall_score,
        "pillar_scores": {
            "v2_oauth_auth": round(auth_score, 1),
            "order_creation_payload": round(order_score, 1),
            "webhook_signature_verification": round(webhook_score, 1),
            "server_status_reconciliation": round(status_score, 1)
        },
        "findings": findings,
        "recommendations": recommendations
    }


def main():
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()
    if not target.exists():
        print(f"Error: Target path '{target}' does not exist", file=sys.stderr)
        sys.exit(1)

    result = audit_project(target)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
