---
name: offline-first-sync
description: Mobile Data Synchronization Protocol for offline-first architectures, local persistence, change data capture, conflict resolution, and resilient transport.
version: 1.0.0
type: intelligence
status: internal
---

# Mobile Data Synchronization Protocol (`offline-first-sync`)

## 1. Role and Core Purpose
The **Mobile Data Synchronization Protocol** skill (`offline-first-sync`) provides AI engineering agents with authoritative architectural patterns, invariants, schemas, and verification tooling to implement robust offline-first synchronization across mobile and cross-platform applications (Flutter, React Native, iOS Swift, Android Kotlin).

### Core Architectural Responsibilities
- **Local-First Authoritative Reads**: UI layers bind exclusively to reactive local databases (SQLite, Room, SQLCipher, WatermelonDB, PowerSync); never block UI rendering on remote network calls.
- **Transactional Mutation Outbox**: Capture local mutations synchronously within the same ACID transaction as the state change using client-generated UUID v4 idempotency keys.
- **Tombstones & Safe Deletion**: Eliminate zombie record resurrects via soft-delete tombstones (`is_deleted = 1`) and deferred garbage collection.
- **Deterministic Conflict Arbitration**: Resolve multi-device concurrent edits using deterministic Field-Level Last-Write-Wins (LWW) with Lamport/Vector Clocks or Conflict-Free Replicated Data Types (CRDTs).
- **Transport Resilience & Thundering Herd Protection**: Network pipeline with truncated exponential backoff, full randomized jitter, reachability triggers, and delta pagination.

---

## 2. Command Specifications

### `/audit-sync-protocol [path-to-mobile-project]`
Audits a mobile codebase across the 4 sync pillars (Local Persistence, CDC Outbox, Conflict Resolution, Transport Resilience) and outputs a JSON report and markdown summary.

```bash
python3 engineering/mobile/offline-first-sync/scripts/audit_sync_protocol.py [target-dir]
```

### `/scaffold-sync-engine [framework]`
Generates standardized SQL schemas and sync outbox handlers conforming to `templates/sync-schema.sql`.

### `/verify-sync-invariants`
Validates that client-side sync operations preserve causal consistency, idempotency, and network partition tolerance.

---

## 3. Four Protocol Pillars & Invariants

### Pillar 1: Local Persistence & Storage (25 Pts)
- **Invariant**: The local embedded database is the single source of truth for the client presentation layer.
- **Tombstones**: Soft delete flag (`is_deleted`) required for all entities synchronized with a remote server. Deletions propagate across peers as explicit tombstone records before garbage collection.

### Pillar 2: Change Data Capture (CDC) & Outbox Queue (25 Pts)
- **Invariant**: Every user-initiated change creates a persistent mutation log entry in the same atomic database transaction as the entity mutation.
- **Client Idempotency**: Each mutation carries a client-generated UUID v4 `mutation_id`. The server records applied IDs to guarantee exact-once processing semantics across network retries.

### Pillar 3: Conflict Resolution & Versioning (25 Pts)
- **Invariant**: Concurrent divergent updates must converge deterministically across all peers without data loss or infinite synchronization loops.
- **Resolution Strategy**:
  1. *State-based CRDTs* for collaborative sets, counters, and text.
  2. *Field-Level LWW* with hybrid logical clocks (HLC) where CRDT overhead is prohibitive.
  3. *Three-Way Merge* with interactive user resolution for irreversible business domain states.

### Pillar 4: Transport Resilience & Backoff (25 Pts)
- **Invariant**: Sync reconnections must prevent server DDoS through exponential backoff with full jitter:
  $$\text{Interval} = \text{random}(0, \min(\text{max\_backoff}, \text{base} \times 2^{\text{retry}}))$$
- **Network Awareness**: Bind sync worker activation to OS connectivity broadcast changes (e.g. `ConnectivityManager` / `NWPathMonitor`).
