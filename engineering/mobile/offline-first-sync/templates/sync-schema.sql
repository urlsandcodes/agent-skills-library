-- Offline-First Local Store Baseline Schema
-- SQLite / Room / SQLCipher with Change Tracking & Tombstones

CREATE TABLE IF NOT EXISTS local_metadata (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS sync_mutation_log (
    mutation_id TEXT PRIMARY KEY,       -- UUID v4 client-generated mutation ID (Idempotency Key)
    entity_type TEXT NOT NULL,          -- e.g., 'document', 'message', 'profile'
    entity_id TEXT NOT NULL,            -- Canonical UUID of the record
    operation TEXT NOT NULL,            -- 'INSERT', 'UPDATE', 'DELETE'
    payload JSON NOT NULL,              -- State or delta delta payload
    client_timestamp INTEGER NOT NULL,  -- Local unix millis
    version INTEGER NOT NULL,           -- Local client sequence version
    sync_status TEXT NOT NULL,          -- 'PENDING', 'IN_FLIGHT', 'COMMITTED', 'REJECTED'
    retry_count INTEGER DEFAULT 0,      -- Backoff retry tracking
    last_error TEXT                     -- Diagnostic failure message if rejected
);

CREATE INDEX IF NOT EXISTS idx_mutation_status ON sync_mutation_log(sync_status, client_timestamp);

-- Example Entity Table with Tombstones and Versioning
CREATE TABLE IF NOT EXISTS syncable_entities (
    id TEXT PRIMARY KEY,
    entity_type TEXT NOT NULL,
    data JSON NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    client_updated_at INTEGER NOT NULL,
    server_updated_at INTEGER,
    is_deleted INTEGER NOT NULL DEFAULT 0 -- Soft-delete tombstone
);

CREATE INDEX IF NOT EXISTS idx_entity_sync ON syncable_entities(is_deleted, client_updated_at);
