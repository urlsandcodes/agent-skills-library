---
name: testing.missed-case-detector
description: Inspects architectural flows, invariants, and state transitions against existing test suites to identify uncovered edge cases, failure modes, and race conditions.
version: 1.0.0
type: intelligence
status: internal
---

# Flow & Edge-Case Test Gap Detector

## 1. Role and Core Purpose
The **Flow & Edge-Case Test Gap Detector** (`testing.missed-case-detector`) acts as an elite QA automation architect and testing strategist.

Instead of measuring superficial line-coverage percentages, it evaluates **architectural flow coverage**:
- Reads the living architectural ground truth in `.agents/architecture.md`.
- Inspects all existing test files across the repository (`test-*.js`, `*.test.js`, `*.spec.ts`, etc.).
- Compares each critical flow and shared-state boundary against the test suite.
- Uncovers missing negative tests, race condition checks, idempotency replays, and background worker failure handling.
- Synthesizes concrete, actionable test cases with assertions ready to implement.

---

## 2. When to Activate This Skill
Agents should trigger this skill whenever:
- The user requests: `/detect-test-gaps`, "find missed test cases", "audit test coverage against architecture", or "what tests are we missing?".
- A new flow or architectural domain is added to `.agents/architecture.md`.
- Preparing a test plan or regression hardening cycle before production release.

---

## 3. Command Specification: `/detect-test-gaps`

### Execution Workflow

#### Step 1: Ingest Living Architecture
Locate and read `.agents/architecture.md` (or the path specified by the user).
Extract:
- Identified flows (Intake, Ingestion, Processing, Fulfillment, Workers).
- Shared state entities and concurrency controls.
- Living architectural invariants (`Verified`, `Known Architectural`, `Identified Risk`).

#### Step 2: Scan Existing Test Suites
Search the project for test files:
- Node.js / Jest / Mocha / Vitest / Custom suites: `test-*.js`, `*.test.js`, `*.spec.js`, `tests/**/*.js`.
- Python: `tests/test_*.py`, `*_test.py`.
- Go: `*_test.go`.
Analyze which functions, endpoints, and error paths each test file actually asserts.

#### Step 3: Gap Cross-Referencing Matrix
Systematically evaluate whether tests exist for the following 10 critical gap categories:
1. **Race Conditions**: Are concurrent requests against shared state (e.g. concurrent webhook + browser return) tested with `Promise.all`?
2. **Idempotency Replay**: Does a test send duplicate payloads with the same transaction/order ID to assert zero double-allocation?
3. **Out-of-Order Events**: Does a test simulate the webhook arriving *before* the order is confirmed in the database?
4. **Worker Failure & Retry**: Does a test simulate external service timeouts (e.g. Telegram 429 FLOOD_WAIT, S3 500) and verify outbox retry status?
5. **Partial Failure & Rollbacks**: If payment succeeds but entitlement allocation fails, is the transaction/ledger rollback tested?
6. **Negative Authorization**: Are unauthorized callers explicitly tested against each sensitive domain endpoint?
7. **State Machine Skips**: Are invalid state transitions (e.g. transitioning directly from `cancelled` to `completed`) asserted to fail?
8. **Boundary & Missing Input**: Are null, empty, or truncated payloads tested against validation schemas?
9. **Grace Period & Expiry**: Are worker expiry calculations tested with mock time across boundary timestamps?
10. **Silent Failures**: Does every catch block have assertions verifying proper logging and non-zero HTTP error codes?

#### Step 4: Output Canonical Artifacts
1. Machine-readable JSON array of test gaps conforming to `schemas/test-gap.schema.json`.
2. Comprehensive markdown report generated using `templates/test-gap-report.md` and saved to `.agents/test-gap-report.md`.
