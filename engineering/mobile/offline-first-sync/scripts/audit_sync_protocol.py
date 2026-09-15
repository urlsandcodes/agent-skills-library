#!/usr/bin/env python3
"""Audit a mobile/client repository for Offline-First Data Synchronization Protocol compliance."""

from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys
from typing import Any, Dict, List


def audit_project(target_dir: Path) -> Dict[str, Any]:
    findings: List[Dict[str, Any]] = []
    
    # Pillar 1: Local Persistence & Storage (25 pts)
    local_score = 0.0
    # Search for sqlite, room, realm, core data, watermelondb, powersync, indexeddb
    has_local_db = False
    has_tombstone = False
    has_indexing = False
    
    # Pillar 2: Change Data Capture (CDC) & Mutation Queue (25 pts)
    cdc_score = 0.0
    has_mutation_queue = False
    has_idempotency_keys = False
    
    # Pillar 3: Conflict Resolution (25 pts)
    conflict_score = 0.0
    has_conflict_logic = False
    
    # Pillar 4: Transport Resilience & Backoff (25 pts)
    resilience_score = 0.0
    has_backoff_retry = False
    has_network_listener = False

    # Scan project source files
    valid_exts = {".ts", ".tsx", ".js", ".jsx", ".kt", ".swift", ".dart", ".java", ".py", ".sql"}
    
    for file_path in target_dir.rglob("*"):
        if not file_path.is_file() or file_path.suffix not in valid_exts:
            continue
        if any(part in file_path.parts for part in [".git", "node_modules", "dist", "build", ".venv"]):
            continue
            
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
            
        # Check Local DB
        if any(k in content.lower() for k in ["sqlite", "room", "watermelondb", "sqldelight", "powersync", "realm", "indexeddb", "rxdb", "coredata"]):
            has_local_db = True
            
        if any(k in content.lower() for k in ["is_deleted", "isdeleted", "deleted_at", "deletedat", "tombstone"]):
            has_tombstone = True
            
        if any(k in content.lower() for k in ["create index", "addindex", "@index", "primary key"]):
            has_indexing = True
            
        # Check CDC & Mutations
        if any(k in content.lower() for k in ["mutation", "outbox", "sync_queue", "synclog", "pending_ops", "pendingoperations"]):
            has_mutation_queue = True
            
        if any(k in content.lower() for k in ["idempotency", "mutation_id", "mutationid", "uuid", "client_id", "tx_id"]):
            has_idempotency_keys = True
            
        # Check Conflict Resolution
        if any(k in content.lower() for k in ["conflict", "crdt", "vector_clock", "last_write_wins", "lww", "version", "rev", "3-way"]):
            has_conflict_logic = True
            
        # Check Transport Resilience
        if any(k in content.lower() for k in ["backoff", "exponential", "jitter", "retry"]):
            has_backoff_retry = True
            
        if any(k in content.lower() for k in ["netinfo", "reachability", "connectivity", "online", "networkstatus"]):
            has_network_listener = True

    # Compute Pillar 1 (Local Persistence)
    if has_local_db:
        local_score += 10.0
        findings.append({
            "id": "SYNC-LP-01",
            "pillar": "local_persistence",
            "status": "pass",
            "title": "Local Persistence Engine Configured",
            "details": "Detected embedded database or reactive local persistence layer.",
            "remediation": "Maintain pure local read/write paths."
        })
    else:
        findings.append({
            "id": "SYNC-LP-01",
            "pillar": "local_persistence",
            "status": "fail",
            "title": "Missing Local Persistent Store",
            "details": "No embedded SQLite, Room, WatermelonDB, or local store detected.",
            "remediation": "Integrate an embedded transactional local database for offline-first operation."
        })

    if has_tombstone:
        local_score += 10.0
        findings.append({
            "id": "SYNC-LP-02",
            "pillar": "local_persistence",
            "status": "pass",
            "title": "Tombstone (Soft Delete) Schema Pattern",
            "details": "Detected soft delete flags for safe deletion synchronization.",
            "remediation": "Retain tombstones until verified upstream acknowledgement."
        })
    else:
        findings.append({
            "id": "SYNC-LP-02",
            "pillar": "local_persistence",
            "status": "warn",
            "title": "Missing Tombstone Deletion Handling",
            "details": "Hard deletes can cause resurrected records during synchronization.",
            "remediation": "Implement soft delete tombstones (e.g. is_deleted=1) with GC after sync."
        })

    if has_indexing:
        local_score += 5.0

    # Compute Pillar 2 (CDC & Outbox Queue)
    if has_mutation_queue:
        cdc_score += 15.0
        findings.append({
            "id": "SYNC-CDC-01",
            "pillar": "change_data_capture",
            "status": "pass",
            "title": "Transactional Mutation Outbox Present",
            "details": "Local modifications recorded into mutation queue for asynchronous sync.",
            "remediation": "Ensure outbox mutations are committed atomically with local entity updates."
        })
    else:
        findings.append({
            "id": "SYNC-CDC-01",
            "pillar": "change_data_capture",
            "status": "fail",
            "title": "Missing Mutation Outbox Queue",
            "details": "No transactional outbox or sync mutation log detected.",
            "remediation": "Record mutations into a local sync_mutation_log table atomically with local state."
        })

    if has_idempotency_keys:
        cdc_score += 10.0
        findings.append({
            "id": "SYNC-CDC-02",
            "pillar": "change_data_capture",
            "status": "pass",
            "title": "Client-Generated Idempotency Keys",
            "details": "Found client mutation IDs or UUIDs to prevent double-application.",
            "remediation": "Send mutation UUIDs with all synchronization payloads."
        })
    else:
        findings.append({
            "id": "SYNC-CDC-02",
            "pillar": "change_data_capture",
            "status": "warn",
            "title": "Missing Client Mutation UUIDs",
            "details": "Retries without client mutation IDs risk duplicate operations on server.",
            "remediation": "Attach deterministic UUID v4 to every outgoing mutation."
        })

    # Compute Pillar 3 (Conflict Resolution)
    if has_conflict_logic:
        conflict_score = 25.0
        findings.append({
            "id": "SYNC-CR-01",
            "pillar": "conflict_resolution",
            "status": "pass",
            "title": "Conflict Resolution Protocol Implemented",
            "details": "Detected version vectors, LWW timestamp rules, or CRDT logic.",
            "remediation": "Validate tie-breaking monotonicity across client-server clock skews."
        })
    else:
        findings.append({
            "id": "SYNC-CR-01",
            "pillar": "conflict_resolution",
            "status": "fail",
            "title": "Undefined Conflict Resolution Strategy",
            "details": "No explicit conflict arbitration (LWW, Vector Clocks, or CRDT) found.",
            "remediation": "Implement deterministic conflict resolution (e.g. Field-level LWW or CRDTs)."
        })

    # Compute Pillar 4 (Transport Resilience & Backoff)
    if has_backoff_retry:
        resilience_score += 15.0
        findings.append({
            "id": "SYNC-TR-01",
            "pillar": "transport_resilience",
            "status": "pass",
            "title": "Exponential Backoff & Retry Logic Present",
            "details": "Detected backoff algorithm for network failures.",
            "remediation": "Ensure full random jitter is applied to backoff intervals."
        })
    else:
        findings.append({
            "id": "SYNC-TR-01",
            "pillar": "transport_resilience",
            "status": "fail",
            "title": "Missing Resilient Exponential Backoff",
            "details": "Sync attempts on connection restoration may cause thundering herd.",
            "remediation": "Implement exponential backoff with full jitter for network retries."
        })

    if has_network_listener:
        resilience_score += 10.0
        findings.append({
            "id": "SYNC-TR-02",
            "pillar": "transport_resilience",
            "status": "pass",
            "title": "Network Connectivity State Awareness",
            "details": "Monitors network state transitions to pause/resume background sync.",
            "remediation": "Trigger outbox drains immediately upon validated online transitions."
        })
    else:
        findings.append({
            "id": "SYNC-TR-02",
            "pillar": "transport_resilience",
            "status": "warn",
            "title": "No Explicit Network Reachability Listener",
            "details": "Sync engine cannot react proactively to device reconnects.",
            "remediation": "Listen to OS network connectivity events to trigger queue flushes."
        })

    overall_score = round(local_score + cdc_score + conflict_score + resilience_score, 1)

    recommendations = [
        "Store all application state in embedded local storage (SQLite/Room/WatermelonDB) with optimistic UI updates.",
        "Buffer mutations in an ACID-compliant local outbox table with client-generated UUID idempotency keys.",
        "Implement soft-delete tombstones (is_deleted=1) to prevent resurrected records across distributed sync peers.",
        "Arbitrate conflicts using deterministic Field-level Last-Write-Wins (LWW) or conflict-free replicated data types (CRDTs).",
        "Implement truncated exponential backoff with full jitter and network connectivity state hooks."
    ]

    return {
        "target": str(target_dir),
        "audited_at": datetime.now(timezone.utc).isoformat(),
        "overall_score": overall_score,
        "pillar_scores": {
            "local_persistence": round(local_score, 1),
            "change_data_capture": round(cdc_score, 1),
            "conflict_resolution": round(conflict_score, 1),
            "transport_resilience": round(resilience_score, 1)
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
