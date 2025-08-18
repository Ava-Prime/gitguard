#!/usr/bin/env python3
"""Owners index page generation from graph data."""

import psycopg
import os
import pathlib

def emit_owners_index(db_url: str, docs_dir: str = "docs"):
    """Generate owners.md from graph data showing who owns what files and recent activity."""
    q = """
    with t as (
      select n_owner.id owner_id, n_owner.title owner, count(distinct n_file.id) files
      from codex_nodes n_owner
      join codex_edges e on e.src = n_owner.id and e.rel='owns'
      join codex_nodes n_file on n_file.id = e.dst
      where n_owner.ntype='Owner'
      group by 1,2
    ),
    recent as (
      select n_owner.title owner, max(n_pr.data->>'updated_at') as last_seen
      from codex_nodes n_owner
      join codex_edges e1 on e1.src = n_owner.id and e1.rel='owns'
      join codex_edges e2 on e2.dst = e1.dst and e2.rel='touches'
      join codex_nodes n_pr on n_pr.id = e2.src and n_pr.ntype='PR'
      group by 1
    )
    select t.owner, t.files, coalesce(recent.last_seen,'—') last_seen
    from t left join recent using(owner)
    order by t.files desc, t.owner;
    """
    
    with psycopg.connect(db_url) as c, c.cursor() as cur:
        cur.execute(q)
        rows = cur.fetchall()
    
    md = [
        "# People & Ownership\n",
        "| Owner | Files | Recent Activity |",
        "|---|---:|:---|"
    ]
    
    for o, f, ls in rows:
        md.append(f"| `{o}` | {f} | {ls} |")
    
    pathlib.Path(docs_dir, "owners.md").write_text("\n".join(md), encoding="utf-8")