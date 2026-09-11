# Architectural Plan Audit & Enhanced Implementation Plan

> **Audit Target**: {{PLAN_TITLE}}  
> **Auditor**: `architecture.system-validator`  
> **Date**: {{AUDIT_DATE}}  
> **Baseline Reference**: `.agents/architecture.md`

---

## 1. Scope Classification
- **Primary Classification**: {{SCOPE_CLASSIFICATION}}  
  *(Options: `greenfield` | `isolated` | `integrated` | `cross-domain` | `migration` | `refactor` | `behavior-changing`)*
- **Impact Surface**: {{IMPACTED_DOMAINS}}

---

## 2. Differential Analysis
Systematic comparison of related paths to ensure consistent business rules and prevent unintended divergent behavior:

| Comparative Dimension | Existing Path Behavior | Proposed Path Behavior | Divergence Justification / Invariant |
| :--- | :--- | :--- | :--- |
| **Create vs. Edit** | Requires non-null tenant ID | Editable without tenant ID? | **Violation**: Tenant ID must remain immutable. |
| **Initial Call vs. Retry** | Generates new idempotency key | Reuses key or lacks header? | **Requirement**: Client retry must reuse key. |
| **Sync vs. Async Handler** | Returns immediate response | Dispatches to worker | **Requirement**: Status polling or webhook ack needed. |

---

## 3. Canonical Edge-Case Evaluation Matrix

```json
[
  {
    "id": "EDGE-001",
    "category": "race-condition",
    "scenario": "Webhook arrives before browser confirms payment",
    "severity": "high",
    "status": "missing",
    "affected_components": ["payment", "order", "entitlement"],
    "claim": "Plan assumes browser redirect finishes before webhook fires.",
    "evidence": {
      "source_type": "plan",
      "location": "plan.md#L45",
      "details": "No concurrency lock or idempotency check on payment status transition."
    },
    "required_behavior": "Webhook processing must independently complete payment fulfillment safely.",
    "verification_method": "Integration test with concurrent webhook and redirect execution."
  }
]
```

---

## 4. Audit Findings Summary

| ID | Category | Severity | Status | Affected Component | Required Action |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **EDGE-001** | `race-condition` | `high` | **Required** | `PaymentService` | Add optimistic locking to order status. |
| **EDGE-002** | `stale-state` | `medium` | **Risk** | `CacheManager` | Add cache invalidation hook on update. |
| **EDGE-003** | `validation-boundary` | `high` | **Verified** | `InputValidator` | Verified: Joi schema validates all inputs. |

*Status Legend:*
- **Verified**: Demonstrably handled by existing code/tests.
- **Required**: Implementation plan must explicitly address it.
- **Risk**: Architectural risk requiring monitoring or mitigation.
- **Unknown**: Insufficient evidence to verify. *(Never assumed to be verified).*

---

## 5. Enhanced Implementation Plan

### 5.1 Architecture Impact & Affected Components
- Affected Domains: {{AFFECTED_DOMAINS}}
- New/Modified Persistence: {{PERSISTENCE_CHANGES}}

### 5.2 Required Code Changes & Remediations
1. **Domain Logic Updates**: Implement core business flow changes.
2. **Edge-Case Mitigations**: Implement mitigations for all items marked `Required` in Section 4.
3. **Invariants Enforcement**: Ensure all living invariants in `.agents/architecture.md` are satisfied.

### 5.3 Test & Verification Requirements
- **Unit Tests**: Coverage for isolated business rules and validation boundaries.
- **Differential Tests**: Explicit test asserting consistent behavior between related paths (e.g. Create vs Edit).
- **Edge-Case Tests**: Deterministic test for each `Required` edge-case finding.

### 5.4 Observability Requirements
- Metrics: Counter for success/failure/retries.
- Traces: Distributed span propagation across queue and external API calls.
- Structured Logs: Correlated transaction IDs.

### 5.5 Rollback & Migration Considerations
- Safe rollback plan: Revert strategy if post-deploy failure occurs.
- Data migration backward-compatibility: Column/field additions must be backward-compatible with running instances.
