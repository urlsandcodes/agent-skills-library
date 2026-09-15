---
name: fintech-payments-phonepe
description: Official PhonePe Payment Gateway (V2 API) integration patterns, standard checkout, UPI AutoPay, webhook signature verification, and reconciliation.
version: 1.0.0
type: intelligence
status: internal
---

# PhonePe Payment Gateway Integration Protocol (`fintech-payments-phonepe`)

## 1. Role and Core Purpose
The **PhonePe Payment Gateway Integration** skill (`fintech-payments-phonepe`) equips AI engineering agents with authoritative implementation patterns, strict security invariants, and automated auditing tools for integrating PhonePe Payment Gateway (V2 API) into web and mobile backends.

### Core Architectural Responsibilities
- **V2 OAuth Credentials**: Enforce migration to modern Client ID, Client Secret, and Client Version credential models; explicitly reject deprecated V1 Salt Key (`X-VERIFY`) patterns.
- **Strict Integer Paise Precision**: All transactions are denominated in integer paise ($1\text{ INR} = 100\text{ paise}$) to eliminate IEEE 754 floating-point rounding hazards.
- **Cryptographic Webhook Authenticity**: Enforce server-to-server webhook verification using HMAC-SHA256 evaluated in constant time (`timingSafeEqual`) to prevent timing attacks.
- **Server Status Reconciliation**: Prohibit state mutations based solely on client-side browser redirects; require server-to-server validation via `/v2/order/{merchantOrderId}/status`.

---

## 2. Command Specifications

### `/audit-phonepe-integration [path-to-backend]`
Scans the project codebase across the 4 PhonePe integration pillars (V2 OAuth, Order Creation, Webhook Verification, Status Reconciliation) and generates structured JSON/Markdown audits.

```bash
python3 engineering/fintech/payments-phonepe/scripts/audit_phonepe_integration.py [target-dir]
```

### `/scaffold-phonepe-client [language]`
Deploys a hardened, production-ready PhonePe gateway client based on `templates/phonepe-client.ts`.

### `/verify-phonepe-security`
Verifies that secret credentials, merchant order idempotency keys, and webhook replay protections meet banking-grade compliance standards.

---

## 3. Four Integration Pillars & Invariants

### Pillar 1: Modern V2 OAuth Authentication (25 Pts)
- **Invariant**: Authentication tokens must be requested via `/v1/oauth/token` using `client_id`, `client_secret`, and `client_version`.
- **Deprecated V1 Warning**: Any use of Salt Keys or static SHA-256 header hashing is flagged as a blocking failure.

### Pillar 2: Order Creation Payload & Idempotency (25 Pts)
- **Invariant**: Every payment initiation must submit a client-generated unique `merchantOrderId` to PhonePe `/v2/pay`.
- **Paise Formatting**: Amounts must be non-zero positive integers representing paise.

### Pillar 3: Webhook Verification & Timing Attack Prevention (25 Pts)
- **Invariant**: Inbound webhook notifications must be verified against `client_secret` using HMAC-SHA256 in constant time:
  ```typescript
  crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(computed))
  ```

### Pillar 4: Authoritative Server Status Reconciliation (25 Pts)
- **Invariant**: The client-side redirect URL (`redirectUrl`) is strictly an informational presentation route. Orders and credits may only be fulfilled after an authoritative response from `/v2/order/{merchantOrderId}/status` or a verified webhook payload.
