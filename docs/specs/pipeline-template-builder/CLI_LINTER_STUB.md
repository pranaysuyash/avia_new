# Pipeline Linter — Minimal Script Outline (Pseudocode)

The following pseudocode illustrates a minimal implementation that ties together schema validation and rule checks.

```pseudo
main(args):
  cmd, target, flags = parse_args(args)
  files = collect_files(target)
  reporter = select_reporter(flags)
  rules = load_rules(cmd)

  exit_code = 0
  for file in files:
    tpl = read_json(file)
    diagnostics = []

    if 'validate' in rules or 'all' in rules:
      if not json_schema_validate(TEMPLATE_SCHEMA.json, tpl):
        diagnostics += schema_errors()

      if tpl.parameters_schema:
        if not json_schema_validate(tpl.parameters_schema, tpl.parameters):
          diagnostics += param_schema_errors()

    if 'dag' in rules or 'all' in rules:
      diagnostics += check_acyclic(tpl.dag)
      diagnostics += check_edge_refs(tpl.dag)
      diagnostics += check_io_compat(tpl.dag)
      diagnostics += check_size_limit(tpl.dag)

    if 'io' in rules or 'all' in rules:
      diagnostics += check_template_io_contracts(tpl.io, tpl.dag)

    if 'policy' in rules or 'all' in rules:
      diagnostics += check_prepublish_policies(tpl)
      diagnostics += check_latency_budgets(tpl)

    reporter.print(file, diagnostics)
    if any(d.severity == 'ERROR' for d in diagnostics):
      exit_code = 1

  exit(exit_code)
```

Rule sketches:
- `check_acyclic`: run DFS/toposort and detect back-edges
- `check_edge_refs`: verify edge `from`/`to` endpoints point to existing node ports
- `check_io_compat`: compare producer `io.out` vs consumer `io.in` type strings
- `check_template_io_contracts`: ensure template-level IO mirrors DAG inputs/outputs
- `check_prepublish_policies`: ensure policy gates before Publish/Export nodes
- `check_latency_budgets`: ensure `Detect.Highlights`-like nodes have latency budgets

Reporters:
- text: human-readable with file:line (if available), rule_id, severity, message
- json: machine-readable list with fields (file, rule_id, severity, message, location, node_id)
- summary: aggregate counts by rule and severity

```shell
# Examples
pipeline-lint all docs/specs/pipeline-template-builder/examples/*.json --summary
pipeline-lint dag docs/specs/pipeline-template-builder/examples/QC_PACK.json --json
```

