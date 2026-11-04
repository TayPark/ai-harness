# TayPark Skills

Reusable agent skills for planning, assessing, and executing software implementation work.

Version: `v0.1b` = `v0.1` plus the Independent Workflow Verifier.

## Included skills

| Skill | Use it when |
| --- | --- |
| `spec-driven-development/00-orchestration/implementation-workflow-orchestrator` | You need to coordinate substantial work from planning through verified handoff. |
| `spec-driven-development/01-plan/repository-implementation-planner` | You need a read-only, repository-grounded implementation plan. |
| `spec-driven-development/02-assessment/implementation-spec-assessor` | You need evidence-based review or refinement of an implementation specification. |
| `spec-driven-development/03-execution-and-verification/implementation-plan-executor` | You approved a multi-phase plan and want its work implemented and verified. |
| `spec-driven-development/04-independent-verification/independent-workflow-verifier` | You need a separate reviewer to verify implementation evidence and acceptance criteria. |

## Recommended workflow

For substantial work, start with the Orchestrator. It coordinates this sequence:

1. Ask the Planner for a read-only plan.
2. Ask the Assessor to evaluate the exact plan text.
3. Require a READY assessment, then approve the same plan version and scope.
4. Ask the Executor to carry out the approved phases and update the durable workflow record.
5. Ask a different subagent to run the Independent Workflow Verifier. Close the workflow only after `PASS`.

The Planner marks new plans `PENDING_USER_APPROVAL`. Plan creation or review does not approve execution. An explicit current-session request to implement an identified plan is approval. The Executor records that instruction and its scope.

For a small, direct implementation request that does not need a formal plan, implement and verify it directly. Do not require the full sequence for that request.

## Install

Copy the Orchestrator folder into your agent's skill directory to use it as the entry point. For Codex, the default directory is `~/.codex/skills/`.

```sh
cp -R spec-driven-development/00-orchestration/implementation-workflow-orchestrator ~/.codex/skills/
```

Install the Planner, Assessor, Executor, and Independent Workflow Verifier folders too when you want the Orchestrator to coordinate them. Each installed folder keeps its canonical skill name. Check each destination first.

For a local checkout, link the five skills into Codex instead of copying them. Run these commands from the repository root after confirming that the destination names are free. Move any existing skill folders outside `~/.codex/skills/` first.

```sh
mkdir -p ~/.codex/skills
ln -s "$PWD/spec-driven-development/01-plan/repository-implementation-planner" ~/.codex/skills/repository-implementation-planner
ln -s "$PWD/spec-driven-development/02-assessment/implementation-spec-assessor" ~/.codex/skills/implementation-spec-assessor
ln -s "$PWD/spec-driven-development/03-execution-and-verification/implementation-plan-executor" ~/.codex/skills/implementation-plan-executor
ln -s "$PWD/spec-driven-development/00-orchestration/implementation-workflow-orchestrator" ~/.codex/skills/implementation-workflow-orchestrator
ln -s "$PWD/spec-driven-development/04-independent-verification/independent-workflow-verifier" ~/.codex/skills/independent-workflow-verifier
```

## Requirements

The Planner, Executor, Orchestrator, and Independent Workflow Verifier use Markdown instructions and have no runtime dependencies. The Assessor's scripts and tests require Python 3.11 or newer. Install its pinned dependencies in an isolated environment:

```sh
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -r spec-driven-development/02-assessment/implementation-spec-assessor/requirements.txt
```

## Validate

Run the repository checks from the repository root:

```sh
python scripts/validate_public_package.py
```

Run the Assessor tests and report validator from its folder:

```sh
cd spec-driven-development/02-assessment/implementation-spec-assessor
python -m pytest -q
python scripts/validate_assessment.py --report tests/fixtures/reports/excellent.json --source tests/fixtures/excellent-prompt.md
```

The scenario files under each skill's `tests/` folder describe manual behavior checks. They are not automated test suites.

## License

MIT. See [LICENSE](LICENSE).
