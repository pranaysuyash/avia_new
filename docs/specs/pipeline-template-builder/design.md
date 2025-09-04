# Pipeline & Template Builder Platform — Design

## Architecture Overview
- Canvas Editor (frontend): DAG builder with node palette, inspector panel, template manager.
- Compiler: Validates DAG (acyclic, type-safe IO), generates an execution plan with node configs.
- Orchestrator Adapter: Submits plan to existing job system (queues/workers), tracks run state.
- Catalog: Node definitions (IO schemas, param schema, cost/time estimator).
- Policy Engine: Executes preconditions and approval gates.
- Telemetry: Collects per-node/run metrics and logs; exposes via API.
- Registry: Stores templates, versions, manifests, policies, triggers.

## Node Model
- NodeDef(id, name, category, inputs[], outputs[], params_schema, estimator)
- NodeInstance(id, def_id, params, ui)
- Edge(from_node.port, to_node.port)

## DAG Validation
- Acyclicity check; port type compatibility; required params; policy placement (gates before publish/export).

## Compilation
- Build topologically sorted stages; attach idempotency keys; generate retries/backoff policies.
- Resolve secrets references; attach cost/time estimates with confidence.

## Execution Flow
1) User selects template version and trigger.
2) Compiler generates plan and checks contracts.
3) Adapter submits plan; per-node jobs created (fan-out/fan-in) using existing queue.
4) Telemetry service streams progress; UI updates live.
5) On failures, policy decides: retry, skip, halt; rerun UI allows partial replay.

## Persistence
- Templates: JSON DAG with nodes/edges + param schema + metadata.
- Manifests: signed JSON for CI; includes IO contracts and checksums.
- Runs: status timeline, node execs with metrics and logs_ref.

## Cost/Time Estimation
- Estimator plugs per node; uses historical metrics and heuristics.
- Display as range (P50/P95) and per-run aggregate.

## Security & Compliance
- RBAC scope: templates, runs, triggers, policies.
- Signed manifests; policy steps enforce PII/redaction/rights checks.
- Audit logs for template changes and run decisions.

## APIs (Selected)
- POST `/api/v1/pipelines/compile` { template_id, version, parameters }
- POST `/api/v1/pipelines/run` { template_id, version, trigger_id?, parameters }
- GET `/api/v1/pipelines/runs/{run_id}` → { status, graph, node_execs[] }
- GET `/api/v1/pipelines/templates/{id}/manifest`
- POST `/api/v1/pipelines/policies` { name, checks[] }

## Scaling Considerations
- Large DAGs: virtualize canvas; server-side pagination for runs.
- Concurrency control per tenant; backpressure from job queues.

## Failure Modes
- Node failure: retry → skip/halt per policy; isolate logs.
- Compile failure: schema violation; actionable errors; suggest fixes.

