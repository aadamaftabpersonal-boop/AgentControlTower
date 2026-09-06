# Agent Control Tower - Claude Model Allocation

## Purpose

Use the Claude models according to the kind of reasoning required:

- **Opus** - architecture, difficult reasoning, high-risk decisions, Entire semantics, final review.
- **Sonnet** - primary implementation and integration.
- **Haiku** - fast, bounded, mechanical work.

The project follows **version-based vertical scaling**:

`V0 -> V1 -> V2 -> ...`

Each version must work and be tested before moving forward.

---

# 1. Opus - Architect / Critical Reasoning

Use Opus for work where a wrong decision can damage the architecture or where deep reasoning across the system is required.

### Opus owns

- Initial Electron/application architecture
- Core data models and contracts
- Entire CLI and Checkpoint architecture
- Agent state model
- Checkpoint semantics
- Checkpoint Reconstruction design
- Checkpoint-grounded prompt generation
- Preventing later-checkpoint information leakage
- Entire Graph investigation and interpretation
- Agent drift/stuck reasoning
- Evidence and trust architecture
- Databricks architecture and tradeoffs
- Major refactors
- Cross-system debugging
- Security/data-integrity decisions
- Final architecture review
- Final hackathon verification

### Do not normally use Opus for

- Simple UI components
- Boilerplate
- Formatting
- Simple tests
- Renaming
- Obvious one-line fixes
- Routine styling

---

# 2. Sonnet - Primary Builder

Sonnet should do **most of the actual coding**.

### Sonnet owns

- Electron implementation
- Frontend/UI implementation
- Agent visualization
- Agent inspection
- Checkpoint timeline
- Commit inspection
- Backend/local services
- Entire CLI integration after architecture is established
- Checkpoint parsing after the schema is defined
- State management
- IPC
- Data transformations
- File-system integration
- LLM integration
- Status engine implementation
- Graph integration implementation
- Handoff prompt generation
- Checkpoint Reconstruction implementation
- Collision detection implementation
- Evidence/trust implementation
- Databricks implementation
- Tests and integration tests
- Error/loading/empty states
- Packaging and `.exe` build
- Normal debugging

### Default rule

If the task is clearly specified and does not require a major architectural decision:

**Use Sonnet.**

---

# 3. Haiku - Fast Utility

Use Haiku only for small, well-bounded tasks.

### Haiku owns

- Boilerplate
- Simple utility functions
- Styling adjustments
- UI copy
- Formatting
- Lint fixes
- Simple type fixes
- Straightforward tests
- Import updates
- Constants
- Simple fixtures/mock data
- README formatting
- Changelog updates
- Comment cleanup
- Mechanical refactors
- Simple rendering fixes

### Never give Haiku primary ownership of

- Architecture
- Checkpoint Reconstruction semantics
- Prompt-grounding rules
- Entire Graph interpretation
- Agent-status reasoning
- Databricks architecture
- Security-sensitive decisions
- Large refactors
- Final verification

---

# 4. Version-by-Version Allocation

## V0 - Foundation

**Opus:** application architecture, core contracts, Electron/backend boundaries.

**Sonnet:** project setup, Electron, frontend, backend, build pipeline, first `.exe`.

**Haiku:** boilerplate, config cleanup, simple scripts.

## V1 - Single Agent Control Tower

**Opus:** canonical Agent model and evidence-based state definition.

**Sonnet:** agent ingestion, agent world/cards, live updates, basic statuses.

**Haiku:** styling, icons, fixtures, small UI fixes.

## V2 - Agent Inspection

**Opus:** inspection hierarchy and evidence relationships.

**Sonnet:** agent detail view, prompt/files/commits/checkpoints, checkpoint trail.

**Haiku:** UI polish and small refactors.

## V3 - LLM Understanding

**Opus:** grounding strategy and inference boundaries.

**Sonnet:** LLM integration, commit explanations, task summaries, evidence display.

**Haiku:** response formatting and prompt helpers.

## V4 - Status Intelligence

**Opus:** ON TRACK / DRIFTING / STUCK / DONE semantics and confidence rules.

**Sonnet:** status engine, explanations, UI, tests.

**Haiku:** badges, fixtures, simple tests.

## V5 - Entire Graph Intelligence

**Opus:** Graph investigation, relevant relationships, impact-analysis design, validation strategy.

**Sonnet:** Graph integration, evidence display, impact-analysis workflows.

**Haiku:** rendering/formatting helpers.

## V6 - Handoff

**Opus:** checkpoint-grounded handoff semantics and context boundaries.

**Sonnet:** handoff generation, ready-to-use prompts, copy/export workflow, fresh-agent UI.

**Haiku:** prompt presentation and polish.

## V7 - Checkpoint Reconstruction ⭐

**Opus:** reconstruction semantics, temporal boundary, leakage prevention, reconstruction prompt design, verification strategy.

**Sonnet:** checkpoint selection, state extraction, reconstruction prompt generation, reconstruction UI, verification workflow.

**Haiku:** UI polish, formatting, small helpers, fixtures.

**Important:** the core reconstruction reasoning must not be delegated to Haiku.

## V8 - Two-Agent Live World

**Opus:** concurrency/state model review.

**Sonnet:** multiple agents, simultaneous activity, state updates, visualization.

**Haiku:** fixtures and visual tweaks.

## V9 - Agent Collision Detection

**Opus:** collision semantics and meaningful-vs-harmless overlap.

**Sonnet:** collision detection, warnings, affected-file views, tests.

**Haiku:** warning UI and fixtures.

## V10 - Evidence / Trust Layer

**Opus:** evidence hierarchy, verified vs inferred information, confidence rules.

**Sonnet:** evidence objects, source references, confidence display, verification states.

**Haiku:** labels, formatting, mechanical changes.

## V11 - Checkpoint Timeline

**Opus:** temporal model and timeline semantics.

**Sonnet:** timeline, navigation, state transitions, UI.

**Haiku:** styling and small fixes.

## V12 - Databricks Historical Memory

**Opus:** Databricks role, data model, ingestion/query architecture, similarity/retrieval design, tradeoffs.

**Sonnet:** Databricks integration, pipeline, queries, historical-memory UI, curveball behavior.

**Haiku:** fixtures, SQL formatting, UI polish.

## V13 - Reconstruction Verification

**Opus:** fidelity criteria and verification methodology.

**Sonnet:** reconstruction-vs-actual comparison, verification results, pass/fail/uncertain states.

**Haiku:** formatting, fixtures, UI polish.

## V14 - Replay

**Opus:** replay semantics and temporal correctness.

**Sonnet:** replay implementation, state transitions, controls, visualization.

**Haiku:** controls, styling, small fixes.

---

# 5. Cross-Cutting Allocation

| Work | Model |
|---|---|
| Architecture | Opus |
| Major design decisions | Opus |
| Entire/Checkpoint semantics | Opus |
| Graph reasoning | Opus |
| Reconstruction semantics | Opus |
| Evidence/trust rules | Opus |
| Databricks architecture | Opus |
| Normal feature implementation | Sonnet |
| Frontend | Sonnet |
| Backend | Sonnet |
| Integration | Sonnet |
| Tests | Sonnet |
| Packaging | Sonnet |
| Normal debugging | Sonnet |
| Boilerplate | Haiku |
| Styling tweaks | Haiku |
| Formatting | Haiku |
| Fixtures | Haiku |
| Mechanical refactors | Haiku |
| Final system review | Opus |

---

# 6. Recommended Operating Loop

```text
Opus
  ↓
Architecture / difficult reasoning
  ↓
Sonnet
  ↓
Implementation
  ↓
Sonnet
  ↓
Tests + integration
  ↓
Haiku
  ↓
Mechanical cleanup / polish
  ↓
Opus
  ↓
Critical review when required
  ↓
Stable version
  ↓
Next version
```

Do **not** automatically use all three models on every task.

Use the cheapest model that can safely handle the task.

---

# 7. Entire and Checkpoint Rule

Entire evidence remains the source of truth:

- Checkpoints
- Original intent/prompts
- Commits
- Files
- Tests
- Entire Graph evidence

LLMs interpret this evidence. They must not invent unsupported project state.

For high-risk interpretation, Opus defines the reasoning and Sonnet implements it.

---

# 8. Checkpoint Reconstruction Rule

A reconstruction generated from checkpoint `C_n` may use only information available at or before `C_n`.

It must not use:

- Later checkpoints
- Later commits
- Later agent decisions
- Later file states
- Later conclusions
- Information learned after the selected checkpoint

The generated reconstruction must initially be labeled:

**UNVERIFIED**

until fidelity verification is completed.

Opus owns the semantic boundary. Sonnet implements it. Haiku may only perform mechanical work around it.

---

# 9. Escalation Rule

Start with Sonnet unless the task is clearly architectural.

Escalate to Opus when:

- A bug survives multiple reasonable fixes
- Multiple modules disagree about the source of truth
- A core data contract must change
- Entire semantics are unclear
- Checkpoint temporal reasoning is involved
- Reconstruction could leak future information
- Graph evidence contradicts source/test evidence
- Agent status is ambiguous
- Databricks architecture needs to change
- A major refactor is being considered
- The final demo path fails in a non-obvious way

Do not use Opus simply because a task is large.

Use Opus because it requires **deep reasoning or architectural judgment**.

---

# 10. Hackathon Rule

Prioritize:

1. Working end-to-end product
2. Entire workflow correctness
3. Checkpoint-grounded intelligence
4. Noon Curveball readiness
5. Meaningful tests
6. Demo reliability
7. Visual polish

Do not spend expensive model calls polishing a feature that does not work end-to-end.

---

# Final Principle

### Opus thinks.
### Sonnet builds.
### Haiku cleans.

Claude Code remains the primary implementation environment.

The models are different reasoning levels within the same versioned engineering process, not separate developers building competing applications.

Every completed version must leave the codebase in a working state.
