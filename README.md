# TayPark Skills

Reusable agent skills for planning, assessing, implementing, verifying, and releasing software changes.

Version: `v0.2.1`.

## Included skills

| Skill | Use it when |
| --- | --- |
| `spec-driven-development/00-orchestration/implementation-workflow-orchestrator` | You need to coordinate substantial work from specification through release readiness. |
| `spec-driven-development/01-plan/repository-implementation-planner` | You need a read-only, repository-grounded implementation plan. |
| `spec-driven-development/02-assessment/implementation-spec-assessor` | You need evidence-based review or refinement of an implementation specification. |
| `spec-driven-development/03-execution-and-verification/implementation-plan-executor` | You approved a multi-phase plan and want its work implemented and verified. |
| `spec-driven-development/04-independent-verification/independent-workflow-verifier` | You need a separate reviewer to verify implementation evidence and acceptance criteria. |
| `spec-driven-development/05-release-readiness/release-readiness-assessor` | You need an evidence-based release decision after Independent Verification and before publication. |
| `chatgpt-rubric-evaluator` | You need a privacy-filtered packet and locally validated ChatGPT review. |

`career-management` and `.sdd-local/` are local-only and are excluded from the public package.

## Recommended workflow

For substantial work, start with the Orchestrator. It coordinates this sequence:

1. Establish the exact user specification or build a source-labeled input packet from the request and read-only repository observations.
2. Ask the Planner to draft a read-only plan from that input. Keep the plan source separate from the specification/input packet. The draft plan's authoritative requirement map supports the Spec report but does not count as Plan Gate approval.
3. Run the Assessor's Spec Gate on the exact specification/input packet. Spec Assessment must reach `READY` before Plan Assessment.
4. If Spec Assessment needs revision or is blocked, stop before Plan Assessment, approval, and implementation. Ask the Planner to revise the specification/plan draft, then reassess.
5. After Spec Assessment is `READY`, run the Assessor's Plan Gate on the exact plan and its requirement-to-acceptance-to-task-to-verification mapping.
6. Require a READY Plan Gate result, then approve the same plan version, scope, and hashes.
7. Ask the Executor to implement the approved phases and record sandbox, trace, checkpoint, and verification evidence.
8. Ask a different subagent to run Independent Verification against the frozen candidate. Continue only after `PASS`.
9. Run the Release Readiness Assessor before merge, push, tags, or publication. It requires evidence for SLO disposition, security, rollback, and operations.

The Release Gate uses existing SLO targets and measurements. It allows a row-level N/A only when source evidence shows that no service SLO exists. It does not invent thresholds or use publication results as pre-publication evidence. The manual release scenarios are separate from automated tests; they remain `NOT RUN` in this candidate.

For a small, direct implementation request that does not need a formal plan, implement and verify it directly. Do not require the full sequence for that request.

## Install

Copy the Orchestrator folder into your agent's skill directory to use it as the entry point. For Codex, the default directory is `~/.codex/skills/`.

```sh
cp -R spec-driven-development/00-orchestration/implementation-workflow-orchestrator ~/.codex/skills/
```

Install the Planner, Assessor, Executor, Independent Workflow Verifier, and Release Readiness Assessor folders too when you want the Orchestrator to coordinate all six skills. Each installed folder keeps its canonical skill name. Check each destination first.

Install `chatgpt-rubric-evaluator/` separately when you need ChatGPT review packets and local report validation.

For a local checkout, link the six public skills into Codex instead of copying them. Run these commands from the repository root after confirming that the destination names are free. Move any existing skill folders outside `~/.codex/skills/` first.

```sh
mkdir -p ~/.codex/skills
ln -s "$PWD/spec-driven-development/00-orchestration/implementation-workflow-orchestrator" ~/.codex/skills/implementation-workflow-orchestrator
ln -s "$PWD/spec-driven-development/01-plan/repository-implementation-planner" ~/.codex/skills/repository-implementation-planner
ln -s "$PWD/spec-driven-development/02-assessment/implementation-spec-assessor" ~/.codex/skills/implementation-spec-assessor
ln -s "$PWD/spec-driven-development/03-execution-and-verification/implementation-plan-executor" ~/.codex/skills/implementation-plan-executor
ln -s "$PWD/spec-driven-development/04-independent-verification/independent-workflow-verifier" ~/.codex/skills/independent-workflow-verifier
ln -s "$PWD/spec-driven-development/05-release-readiness/release-readiness-assessor" ~/.codex/skills/release-readiness-assessor
```

## Requirements

The Planner, Executor, Orchestrator, Independent Workflow Verifier, and Release Readiness Assessor use Markdown instructions. The Assessor's scripts and tests require Python 3.11 or newer. The ChatGPT Rubric Evaluator requires Python 3.10 or newer and uses the standard library. Install its pinned dependencies in an isolated environment:

```sh
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -r spec-driven-development/02-assessment/implementation-spec-assessor/requirements.txt
```

## Validate

Run the repository package check and the Assessor and Release Readiness tests from the repository root:

```sh
python scripts/validate_public_package.py
python -m pytest -q spec-driven-development/02-assessment/implementation-spec-assessor/tests
python -m pytest -q spec-driven-development/05-release-readiness/release-readiness-assessor/tests
python -m unittest discover -s chatgpt-rubric-evaluator/tests -v
```

Run the Assessor's report validator from its folder:

```sh
cd spec-driven-development/02-assessment/implementation-spec-assessor
python scripts/validate_assessment.py --report tests/fixtures/reports/excellent.json --source tests/fixtures/excellent-prompt.md
```

The manual release scenario is in `spec-driven-development/05-release-readiness/release-readiness-assessor/scenarios/`. Do not treat it as an automated test or claim it ran without recorded evidence.

## License

MIT. See [LICENSE](LICENSE).
