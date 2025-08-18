from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import psycopg
import os

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET"],
    allow_headers=["*"]
)

@app.get("/graph/pr/{number}")
def pr_graph(number: int):
    """Get graph data for a specific PR including connected nodes and edges."""
    with psycopg.connect(os.getenv("DATABASE_URL")) as c, c.cursor() as cur:
        # Find the PR node
        cur.execute(
            "SELECT id FROM codex_nodes WHERE ntype='PR' AND nkey=%s",
            (f"pr:{number}",)
        )
        row = cur.fetchone()
        if not row:
            return {"nodes": [], "edges": []}
        
        pr_id = row[0]
        
        # Start with the PR node
        nodes = [{
            "ntype": "PR",
            "nkey": f"pr:{number}",
            "title": f"PR #{number}"
        }]
        
        # Get all connected nodes and edges
        cur.execute(
            """SELECT n2.ntype, n2.nkey, n2.title, e.rel
               FROM codex_edges e 
               JOIN codex_nodes n2 ON e.dst = n2.id
               WHERE e.src = %s""",
            (pr_id,)
        )
        
        edges = []
        for ntype, nkey, title, rel in cur.fetchall():
            nodes.append({
                "ntype": ntype,
                "nkey": nkey,
                "title": title
            })
            edges.append({
                "src": f"pr:{number}",
                "dst": nkey,
                "rel": rel
            })
        
        return {"nodes": nodes, "edges": edges}