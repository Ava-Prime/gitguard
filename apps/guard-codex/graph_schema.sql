CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "vector";

-- Nodes
CREATE TABLE IF NOT EXISTS codex_nodes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  ntype TEXT NOT NULL,              -- e.g., PR, Commit, Symbol, ADR, Policy, Incident
  nkey  TEXT NOT NULL,              -- stable unique key (e.g., pr:123, commit:<sha>, symbol:path#name)
  title TEXT,
  data  JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (ntype, nkey)
);

-- Edges
CREATE TABLE IF NOT EXISTS codex_edges (
  src UUID NOT NULL REFERENCES codex_nodes(id) ON DELETE CASCADE,
  dst UUID NOT NULL REFERENCES codex_nodes(id) ON DELETE CASCADE,
  rel TEXT NOT NULL,                -- defines, touches, tested_by, governed_by, implements, affects_perf, caused, mitigated_by
  data JSONB NOT NULL DEFAULT '{}',
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (src, dst, rel)
);

-- Embeddings (optional)
CREATE TABLE IF NOT EXISTS codex_embeddings (
  node_id UUID PRIMARY KEY REFERENCES codex_nodes(id) ON DELETE CASCADE,
  model TEXT NOT NULL DEFAULT 'text-embedding-3-large',
  vector VECTOR(1536)               -- adjust to your embedder
);

-- Delivery deduplication table
CREATE TABLE IF NOT EXISTS codex_seen_deliveries (
  delivery_id TEXT PRIMARY KEY,
  received_at TIMESTAMPTZ DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_codex_nodes_type ON codex_nodes(ntype);
CREATE INDEX IF NOT EXISTS idx_codex_nodes_key  ON codex_nodes(nkey);
CREATE INDEX IF NOT EXISTS idx_codex_edges_rel  ON codex_edges(rel);
CREATE INDEX IF NOT EXISTS idx_codex_seen_deliveries_received_at ON codex_seen_deliveries(received_at);