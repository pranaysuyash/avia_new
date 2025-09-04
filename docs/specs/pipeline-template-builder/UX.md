# Pipeline & Template Builder Platform — UX Specification

## Information Architecture
- Entry: Pipelines → Templates → New/Clone → Canvas
- Canvas: node palette (left), canvas center, inspector (right), run pane (bottom)
- Template Manager: list, tags, versions, ownership, share dialog

## Components
- Node Card
  - Icon, title, category, status (for runs), quick actions (inspect, duplicate, disable)
- Edge Connector
  - Type badges (Audio/Text/Meta), validation on connect
- Inspector Panel
  - Sections: Parameters (form), Policies (checklist), Estimations (cost/time), IO (schemas)
- Minimap & Zoom Controls
- Run Pane
  - Timeline (per-node durations), logs viewer, bottleneck heatmap
- Template Version Diff Viewer
  - Side-by-side node/edge changes; params diffs; policy diffs
- Trigger Scheduler Dialog
  - Modes: Upload, Label, Webhook, Cron; concurrency caps; dry-run

## Interactions
- Drag from palette; hold Shift to connect; Esc to cancel connection
- Undo/Redo; multi-select; group nodes; snap to grid; alignment guides
- Keyboard: Space pan; Cmd/Ctrl+Scroll zoom; Enter open inspector; Delete remove
- Validate on-demand and pre-run; show error badges per node/edge

## Visual Language
- Categories color-coded; policies shown as gate nodes; failed nodes in red with tooltip
- Accessibility: focus rings, high-contrast theme, keyboard-first flows

## Empty States & Onboarding
- Starter templates (QC Pack, Creator Pack, Education Pack)
- Guided tour for first pipeline; tooltips for key actions

## Analytics Instrumentation
- Node add/remove; connect/disconnect; parameter changes; validations fired; runs started; run outcomes

