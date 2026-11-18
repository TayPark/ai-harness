# TayPark Skills

Reusable agent skills for planning, assessing, implementing, verifying, and releasing software changes.

Version: `v0.3.0`.

## Included skills

| Skill | Use it when |
| --- | --- |
| `remove-ai-slop` | You need observable AI slop removed while preserving a prose document's format, facts, and voice. |
| `by-subagent` | You need bounded independent workers and want each worker to load only its task-specific skills and evidence. |
| `orchestrate-agent-team` | You need to coordinate a product owner and agent teams for a software project. |
| `interview-for-requirements` | You need to clarify software requirements before planning. |
| `socratic-tutor` | You want structured tutoring or practice toward mastery. |
| `ask-chatgpt` | You need to submit a user-provided question through Aside Browser and return the full response. |
| `ask-to-web-gemini` | You need to submit a user-provided question to Web Gemini (`gemini.google.com`) through Aside CLI using Argon at High thinking level and return the full response. |
| `debate-web-models` | You need Web ChatGPT (highest reasoning) and Web Gemini (Argon High) to run a falsification-driven debate across up to 3 rounds via Aside CLI and synthesize consensus, ruled-out alternatives, and decision boundaries. |
| `sdlc-stage-rubrics` | You need risk-tiered 0–4 rubrics, non-compensatory hard-fail gates, and evidence contracts across Requirement, Implementation, Verification, and Operation. |
| `spec-driven-development/00-orchestration/sdd-00-orchestrate-implementation` | You need to coordinate substantial work from specification through release readiness. |
| `spec-driven-development/01-plan/sdd-01-plan-repository-implementation` | You need a read-only, repository-grounded implementation plan. |
| `spec-driven-development/02-assessment/sdd-02-assess-implementation-spec` | You need evidence-based review or refinement of an implementation specification. |
| `spec-driven-development/03-execution-and-verification/sdd-03-execute-implementation-plan` | You approved a multi-phase plan and want its work implemented and verified. |
| `spec-driven-development/04-independent-verification/sdd-04-verify-implementation-independently` | You need a separate reviewer to verify implementation evidence and acceptance criteria. |
| `spec-driven-development/05-release-readiness/sdd-05-assess-release-readiness` | You need an evidence-based release decision after Independent Verification and before publication. |
| `evaluate-with-chatgpt` | You need a privacy-filtered packet and locally validated ChatGPT review. |

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

## Install, invoke, and update

Run these commands from a trusted checkout. Codex reads `~/.codex/skills/`; Claude Code reads `~/.claude/skills/`. For project-only Claude Code installation use `.claude/skills/` instead. Check destinations first: the loop refuses to overwrite an existing folder or link.

```sh
skill_home="$HOME/.codex/skills" # For Claude Code: "$HOME/.claude/skills"
mkdir -p "$skill_home"
for skill in remove-ai-slop ask-chatgpt ask-to-web-gemini debate-web-models sdlc-stage-rubrics evaluate-with-chatgpt by-subagent orchestrate-agent-team interview-for-requirements socratic-tutor spec-driven-development/*/sdd-*; do
  name="${skill##*/}"
  if [ -e "$skill_home/$name" ] || [ -L "$skill_home/$name" ]; then
    printf 'Already exists: %s\n' "$skill_home/$name" >&2
    continue
  fi
  cp -R "$skill" "$skill_home/$name"
done
```

Start a new session and check the available skills. In Codex, explicitly invoke a skill with `$sdd-01-plan-repository-implementation`. In Claude Code, use `/sdd-01-plan-repository-implementation`. Automatic selection depends on the host and is not guaranteed. Check the host's output when discovery or invocation fails.

For copied installations, update the checkout with `git pull --ff-only`, remove an installed folder only after confirming its contents, and copy the new folder using the same loop. To remove a skill, inspect its path and delete only that installed folder. For symlink installations, update the checkout; the link then points to the updated contents. Renamed folders need new links.

### Migration

Existing invocation names do not remain as compatibility aliases. Remove or relocate an old installed folder or link after inspecting it, then install the corresponding new name. Update local prompts and automation that call the old name.

| Previous name | New name |
| --- | --- |
| `ai-slop-postprocess` | `remove-ai-slop` |
| `ask-to-chatgpt` | `ask-chatgpt` |
| `chatgpt-rubric-evaluator` | `evaluate-with-chatgpt` |
| `codex-team-orchestration` | `orchestrate-agent-team` |
| `requirements-interview` | `interview-for-requirements` |
| `implementation-workflow-orchestrator` | `sdd-00-orchestrate-implementation` |
| `repository-implementation-planner` | `sdd-01-plan-repository-implementation` |
| `implementation-spec-assessor` | `sdd-02-assess-implementation-spec` |
| `implementation-plan-executor` | `sdd-03-execute-implementation-plan` |
| `independent-workflow-verifier` | `sdd-04-verify-implementation-independently` |
| `release-readiness-assessor` | `sdd-05-assess-release-readiness` |

`by-subagent` keeps its name. SDD `00` is the entry point; `02` assesses both specifications and plans. Numbers show a common order, not mandatory steps for every task.

### Selection boundaries

Use each skill for the trigger in the list above. Use `by-subagent` only when delegation is allowed; use `orchestrate-agent-team` for coordinating a team, not a single bounded worker. Use `interview-for-requirements` for unclear requirements, not when sufficient requirements already exist. Use `socratic-tutor` for requested instruction or practice, not a one-off explanation. Use `remove-ai-slop` for observable prose issues, not factual rewriting. Use `ask-chatgpt` to submit a supplied question to ChatGPT, `ask-to-web-gemini` to submit a supplied question to Web Gemini (Argon High), and `debate-web-models` to run a multi-round consensus debate between both web models; use `sdlc-stage-rubrics` for portable 4-stage SDLC scoring and gating definitions; use `evaluate-with-chatgpt` for a bounded, locally validated evaluation. The SDD skills have separate planning, assessment, execution, independent verification and release decisions; skip the formal workflow for a small direct request.

## Requirements

The Planner, Executor, Orchestrator, Independent Workflow Verifier, and Release Readiness Assessor use Markdown instructions. The Assessor's scripts and tests require Python 3.11 or newer. The ChatGPT Rubric Evaluator requires Python 3.10 or newer and uses the standard library. Install its pinned dependencies in an isolated environment:

```sh
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -r spec-driven-development/02-assessment/sdd-02-assess-implementation-spec/requirements.txt
```

## Validate

Run the repository package check and the Assessor and Release Readiness tests from the repository root:

```sh
python scripts/validate_public_package.py
python -m pytest -q spec-driven-development/02-assessment/sdd-02-assess-implementation-spec/tests
python -m pytest -q spec-driven-development/05-release-readiness/sdd-05-assess-release-readiness/tests
python -m unittest discover -s evaluate-with-chatgpt/tests -v
```

Run the Assessor's report validator from its folder:

```sh
cd spec-driven-development/02-assessment/sdd-02-assess-implementation-spec
python scripts/validate_assessment.py --report tests/fixtures/reports/excellent.json --source tests/fixtures/excellent-prompt.md
```

The manual release scenario is in `spec-driven-development/05-release-readiness/sdd-05-assess-release-readiness/scenarios/`. Do not treat it as an automated test or claim it ran without recorded evidence.

## License

MIT. See [LICENSE](LICENSE).
