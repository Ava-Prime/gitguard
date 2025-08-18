package repo.guard

# Weekend freeze (Africa/Johannesburg)
import future.keywords.if

freeze_active {
  # Friday 16:00 → Monday 08:00 local
  t := time.now_ns()
  wday := time.weekday(t)        # 0=Mon ... 6=Sun
  hour := time.clock(t)[0]
  tz := "Africa/Johannesburg"

  # Build local hour/week logic (your existing rule likely already handles this; shown here for clarity)
  # Simplify: Friday >=16, Saturday any, Sunday any, Monday <8
  friday := wday == 4
  saturday := wday == 5
  sunday := wday == 6
  monday := wday == 0

  (friday & hour >= 16) | saturday | sunday | (monday & hour < 8)
}

# Docs conformance guard: if ADR markdown changes, require conformance label or paired code change.
needs_conformance {
  input.action == "merge_pr"
  some p in input.pr.changed_paths
  startswith(p, "docs/adr/")
  not input.pr.labels[_] == "conformance:ok"
  not some c in input.pr.changed_paths; not startswith(c, "docs/")  # i.e., no code change
}