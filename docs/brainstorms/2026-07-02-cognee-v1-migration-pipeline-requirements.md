---
date: 2026-07-02
topic: cognee-v1-migration-pipeline
---

# Cognee v1.0 Migration Pipeline

## Problem Frame

ProjectBrain uses Cognee v0.4 legacy API (`add()+cognify()+search()`) which blocks all v1.0 features. 6 unused features (improve(), truth-subspace reranking, temporal mode, NodeSets, Custom DataModels, MCP server) could dramatically strengthen the self-improving knowledge graph thesis, but the keystone migration must come first. The feedback loop is currently theater — improve() silently no-ops, search returns no scores, and the evolution slider renders static seed data.

## Requirements

### Keystone: v1.0 API Migration
- R1. Replace every `cognee.add()`+`cognee.cognify()` pair with `cognee.remember()` across all 4 files (api.py, server.py, reviewer_agent.py, seed.py).
- R2. Replace every `cognee.search()` with `cognee.recall()`, preserving search type mappings.
- R3. Wire `cognee.improve()` into the mutation path so it fires after every write (not just on manual upvote).

### Truth-Subspace Reviewer
- R4. Replace the keyword matcher in reviewer_agent.py with truth-subspace reranked recall: `cognee.recall(diff_text, search_type=SearchType.TRUTH_SUBSPACE)`.
- R5. CI workflow (projectbrain-review.yml) scores PR diffs by angular distance from the truth centroid instead of substring matching.

### Temporal Evolution Slider
- R6. Backend: Add temporal-scoped API endpoint that calls `cognee.recall(temporal_range=(start, end))` with the slider's time window.
- R7. Frontend: Replace GraphView.tsx hardcoded SEED_ITEMS with live API calls per slider position; re-enable SSE during evolution mode.

### Custom DataModels
- R8. Define Pydantic models: `DecisionModel(title, rationale, files, tags, supersedes, week)` and `ReviewResult(score, patterns_checked, passed)`.
- R9. All write paths accept typed models instead of f-string text blobs. All read paths query by field instead of text-prefix scanning.

### NodeSets
- R10. Replace DATASET+SESSION_DATASET with a single dataset + per-node NodeSet tags (session/permanent, domain labels).
- R11. Eliminate duplicate session/permanent endpoints; routing becomes a NodeSet filter on recall().

### MCP v1.0 Pipeline
- R12. Expand MCP tools to cover the full v1.0 surface (temporal, NodeSet, truth-subspace queries).
- R13. Remove the HTTP notify dance between server.py and api.py — MCP tools call Cognee directly.

## Success Criteria

- All 22 legacy API call sites migrated to v1.0 equivalents.
- improve() fires after every mutation and enriches graph with cross-links.
- A novel anti-pattern (zero keyword overlap with past deprecations) is flagged by the CI reviewer.
- Evolution slider shows real graph state at any time window.
- Decisions can be queried by field (e.g., "all decisions impacting api.py") without text parsing.
- Agents can query the graph by NodeSet, temporal range, and truth-subspace via MCP.

## Scope Boundaries

- No multi-tenant auth (NodeSets used for tagging, not access control).
- No prediction models outside what Cognee provides.
- Existing seed data (weeks 1-8) migrated to new schema but content unchanged.
- Dashboard UI preserved as-is except for evolution slider temporal integration.
- MCP tools expanded but REST endpoints preserved for backward compatibility.

## Key Decisions

- **Atomic migration**: All 22 call sites migrated in one pass (not gradual wrapper). Fastest path to unlock everything.
- **Full pipeline, not minimal**: Implement all 7 features in dependency order. Maximum demo impact.
- **Improve() always-on**: fires after every write, not gated on manual feedback.

## Dependencies

- Cognee v1.0 installed and importable (verify `cognee.remember`, `cognee.recall`, `SearchType.TRUTH_SUBSPACE`, `SearchType.TEMPORAL` exist).
- Pydantic available for custom DataModels.
- No changes to external infra (same Cognee instance, same datasets until migration).

## Next Steps

-> /ce-plan for structured implementation planning with task breakdown.
