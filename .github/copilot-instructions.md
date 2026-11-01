## graphify

For any question about this repo's architecture, structure, components, or how to add/modify/find
code, your first action should be `graphify query "<question>"` when `graphify-out/graph.json`
exists. Use `graphify path "<A>" "<B>"` for relationship questions and `graphify explain "<concept>"`
for focused-concept questions. These return a scoped subgraph, usually much smaller than the full
report or raw grep output.

Triggers: "how do I…", "where is…", "what does … do", "add/modify a <component>",
"explain the architecture", or anything that depends on how files or classes relate.

If `graphify-out/wiki/index.md` exists, use it for broad navigation. Read `graphify-out/GRAPH_REPORT.md`
only for broad architecture review or when query/path/explain do not surface enough context. Only read
source files when (a) modifying/debugging specific code, (b) the graph lacks the needed detail, or
(c) the graph is missing or stale.

Type `/graphify` in Copilot Chat to build or update the graph.

## Ponytail implementation discipline

Apply Ponytail's minimal-change principles to coding tasks: inspect relevant
callers, tests, fixtures, and configuration before editing; reuse existing
implementations; avoid duplicate abstractions and unnecessary dependencies;
keep diffs focused; and retain meaningful validation, error handling, and
security controls. Make the smallest complete change, add focused tests for
non-trivial behavior, and report checks that were skipped and remaining risks.

These project instructions take precedence over any optional Ponytail behavior
that conflicts with ACIS architecture, security, or testing requirements.
Ponytail's source guidance is
[DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail), notably
`skills/ponytail/SKILL.md`; it is integrated as repository guidance rather than
an installed Copilot plugin.

## Combined coding workflow

1. Understand the task and its acceptance criteria.
2. Query Graphify for the relevant architecture and existing implementations.
3. Apply Ponytail's minimal-change principles.
4. Read relevant source and trace the execution flow.
5. Identify security, data-integrity, and compatibility requirements.
6. Implement the smallest complete solution.
7. Add or update focused tests.
8. Run relevant validation and report skipped checks.
9. Update Graphify after source changes and validate that the graph is current.
10. Review the diff for unnecessary or unrelated changes.
11. Commit only when requested or explicitly required by the task.

Graphify's indexed relationships are navigation aids, not proof: confirm
important details in source and tests. The committed graph includes code and
selected architecture Markdown through Graphify's local update path; no LLM or
API enrichment was used. User-maintained task plans are excluded by
`.graphifyignore`. Unsupported files and cross-system relationships may still
be absent.
