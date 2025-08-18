# Semantic Search with pgvector

This document provides SQL examples for performing semantic search using pgvector embeddings.

## Basic Semantic Search Query

Given a query vector `:qv`, find the most similar nodes:

```sql
-- Given a query vector :qv
SELECT ntype, nkey, title, 1 - (vector <=> :qv) AS score
FROM codex_nodes n
JOIN codex_embeddings e ON e.node_id = n.id
ORDER BY e.vector <=> :qv
LIMIT 20;
```

## Advanced Search Queries

### Search within specific node types

```sql
-- Search only PRs
SELECT ntype, nkey, title, 1 - (vector <=> :qv) AS score
FROM codex_nodes n
JOIN codex_embeddings e ON e.node_id = n.id
WHERE n.ntype = 'PR'
ORDER BY e.vector <=> :qv
LIMIT 10;
```

### Search with similarity threshold

```sql
-- Only return results with similarity score > 0.7
SELECT ntype, nkey, title, 1 - (vector <=> :qv) AS score
FROM codex_nodes n
JOIN codex_embeddings e ON e.node_id = n.id
WHERE 1 - (vector <=> :qv) > 0.7
ORDER BY e.vector <=> :qv
LIMIT 20;
```

### Search with metadata filtering

```sql
-- Search PRs with specific labels
SELECT n.ntype, n.nkey, n.title, 1 - (e.vector <=> :qv) AS score,
       n.meta->>'labels' as labels
FROM codex_nodes n
JOIN codex_embeddings e ON e.node_id = n.id
WHERE n.ntype = 'PR' 
  AND n.meta->>'labels' LIKE '%bug%'
ORDER BY e.vector <=> :qv
LIMIT 10;
```

## Vector Operations

### Cosine Distance
The `<=>` operator computes cosine distance (0 = identical, 2 = opposite).

### Cosine Similarity
To get cosine similarity (1 = identical, -1 = opposite):
```sql
SELECT 1 - (vector <=> :qv) AS cosine_similarity
```

### L2 Distance (Euclidean)
```sql
SELECT vector <-> :qv AS l2_distance
```

### Inner Product
```sql
SELECT (vector <#> :qv) * -1 AS inner_product
```

## Performance Tips

1. **Create indexes** for better performance:
   ```sql
   CREATE INDEX ON codex_embeddings USING ivfflat (vector vector_cosine_ops) WITH (lists = 100);
   ```

2. **Use LIMIT** to avoid scanning all vectors

3. **Filter by node type** when possible to reduce search space

4. **Set work_mem** appropriately for large vector operations:
   ```sql
   SET work_mem = '256MB';
   ```

## API Usage

The FastAPI endpoint `/search?q=<query>` automatically:
1. Generates embeddings for the query text
2. Performs the vector similarity search
3. Returns ranked results with similarity scores

Example:
```bash
curl "http://localhost:8000/search?q=authentication%20bug"
```