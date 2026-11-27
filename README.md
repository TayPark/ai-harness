# TayPark Skills

Reusable skills for Codex and Claude Code. Use them to edit prose, consult external models, coordinate agents, or take a software change from requirements through release. Each skill documents when to invoke it and how to run its workflow.

[`skills/`](skills/) holds the source for every packaged skill. Repository-wide checks live in [`scripts/`](scripts/) and [`tests/`](tests/).

Version: `v0.3.0`.

## Included skills

### Writing and editing

| Skill | Use it when |
| --- | --- |
| [`anti-slop`](skills/anti-slop/SKILL.md) | You are drafting English or Korean prose (`draft` mode) or cleaning observable AI slop from a user-supplied document (`postprocess` mode) with deterministic `check_slop.py --strict` and format rubrics. |

### External models and evaluation

| Skill | Use it when |
| --- | --- |
| [`ask-to-chatgpt`](skills/ask-to-chatgpt/SKILL.md) | You want to query Web ChatGPT (highest reasoning) via Aside CLI to conserve local CLI/API tokens. |
| [`ask-to-gemini`](skills/ask-to-gemini/SKILL.md) | You want to query Web Gemini (`Neon High`) via Aside CLI to conserve local CLI/API tokens. |
| [`debate-models`](skills/debate-models/SKILL.md) | You need a falsification-driven 2-model debate (ACH, up to 3 rounds) with explicitly declared peers and transport (`web-pair` via Aside to save local tokens, or `local-pair` via `codex` + `gemini` CLI when tokens are ample). |
| [`evaluate-with-rubric`](skills/evaluate-with-rubric/SKILL.md) | You need a privacy-filtered evidence packet, an independent read-only critic (Aside Web or local CLI), and local deterministic JSON validation. |

### Agent collaboration

| Skill | Use it when |
| --- | --- |
| [`orchestrate-agents`](skills/orchestrate-agents/SKILL.md) | You need bounded subagent delegation with JSON contracts (Tier 1) or multi-team software delivery across a product owner, team leaders, implementers, and independent reviewers (Tier 2). |

### Requirements, implementation, and release

| Skill | Use it when |
| --- | --- |
| [`interview-for-requirements`](skills/interview-for-requirements/SKILL.md) | You need to clarify software requirements before planning. |
| [`sdlc-stage-rubrics`](skills/sdlc-stage-rubrics/SKILL.md) | You need risk-tiered 0–4 rubrics, non-compensatory hard-fail gates, and evidence contracts across Requirement, Implementation, Verification, and Operation. |
| [`sdd-00-orchestrate-implementation`](skills/spec-driven-development/00-orchestration/sdd-00-orchestrate-implementation/SKILL.md) | You need to coordinate substantial work from specification through release readiness. |
| [`sdd-01-plan-repository-implementation`](skills/spec-driven-development/01-plan/sdd-01-plan-repository-implementation/SKILL.md) | You need a read-only, repository-grounded implementation plan. |
| [`sdd-02-assess-implementation-spec`](skills/spec-driven-development/02-assessment/sdd-02-assess-implementation-spec/SKILL.md) | You need evidence-based review or refinement of an implementation specification. |
| [`sdd-03-execute-implementation-plan`](skills/spec-driven-development/03-execution-and-verification/sdd-03-execute-implementation-plan/SKILL.md) | You approved a multi-phase plan and want its work implemented and verified. |
| [`sdd-04-verify-implementation-independently`](skills/spec-driven-development/04-independent-verification/sdd-04-verify-implementation-independently/SKILL.md) | You need a separate reviewer to verify implementation evidence and acceptance criteria. |
| [`sdd-05-assess-release-readiness`](skills/spec-driven-development/05-release-readiness/sdd-05-assess-release-readiness/SKILL.md) | You need an evidence-based release decision after Independent Verification and before publication. |

`career-management` and `.sdd-local/` are local-only and are excluded from the public package.

## External upstream skills

Unmodified third-party skills are linked upstream rather than embedded in this repository:

| Skill | Upstream source | License | Use it when |
| --- | --- | --- | --- |
| `caveman` | [JuliusBrussee/caveman](https://github.com/JuliusBrussee/caveman/blob/main/skills/caveman/SKILL.md) | Apache-2.0 | You want terse responses without losing technical facts. |
| `ponytail` | [DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail/blob/main/skills/ponytail/SKILL.md) | MIT | You want minimal-diff coding discipline and YAGNI guardrails. |
| `socratic-tutor` | [janestreet/agent_skills](https://github.com/janestreet/agent_skills/blob/master/socratic-tutor/SKILL.md) | MIT | You want structured Socratic tutoring or practice toward mastery. |

## Recommended workflow

For substantial work, start with the Orchestrator. It coordinates this sequence:

1. Establish the exact user specification. When goals, user flows, constraints, or acceptance criteria are unclear, run `interview-for-requirements` first to produce a frozen `COMPLETE_BRIEF` (or `PARTIAL_BRIEF` with read-only `Safe Parallel Work`), preserving the original user request and derived brief separately.
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

### One-command multi-host harness bootstrap (Recommended)

Clone this repository on any machine and run `install.sh` to back up existing host configs (`~/.ai-harness-backups/`, `chmod 700`/`600`), compile shared rules (`harness/core/`, `harness/overrides/`) into Antigravity, Claude Code, and Codex, copy managed role contracts (`harness/roles/`), link packaged and pinned upstream skills, and register a non-blocking `SessionStart` auto-sync hook:

```sh
git clone git@github.com:TayPark/skills.git ~/repositories/skills
sh ~/repositories/skills/install.sh
```

Useful maintenance commands (Python 3 standard library only):

```sh
python3 ~/repositories/skills/harness/scripts/harness.py doctor
python3 ~/repositories/skills/harness/scripts/harness.py sync
python3 ~/repositories/skills/harness/scripts/harness.py restore latest
```

### Manual skills-only symlink loop

Run these commands from a trusted checkout if you only want to link `skills/` without compiling host instructions or hooks. Codex reads `~/.codex/skills/`; Claude Code reads `~/.claude/skills/`; Antigravity reads `~/.gemini/config/skills/`. For project-only installation use `.claude/skills/` (Claude Code) or `.agents/skills/` (Antigravity) instead. Check destinations first: the loop refuses to overwrite an existing folder or link.

```sh
skill_home="$HOME/.codex/skills" # Claude Code: "$HOME/.claude/skills" | Antigravity: "$HOME/.gemini/config/skills"
mkdir -p "$skill_home"
for skill in "$PWD"/skills/* "$PWD"/skills/spec-driven-development/*/sdd-*; do
  [ -f "$skill/SKILL.md" ] || continue
  name="${skill##*/}"
  if [ -e "$skill_home/$name" ] || [ -L "$skill_home/$name" ]; then
    printf 'Already exists: %s\n' "$skill_home/$name" >&2
    continue
  fi
  ln -s "$skill" "$skill_home/$name"
done
```

Start a new session and check the available skills. In Codex, explicitly invoke a skill with `$sdd-01-plan-repository-implementation`. In Claude Code, use `/sdd-01-plan-repository-implementation`. Automatic selection depends on the host and is not guaranteed. Check the host's output when discovery or invocation fails.

Update the checkout with `git pull --ff-only` to refresh linked skills. If a link points to the old repository layout, inspect it and replace it with a link to the matching directory under `skills/`. Existing copies require a separate update.

### Migration

Existing invocation names do not remain as compatibility aliases. Remove or relocate an old installed folder or link after inspecting it, then install the corresponding new name. Update local prompts and automation that call the old name.

| Previous name | New name |
| --- | --- |
| `ai-slop-postprocess`, `remove-ai-slop` | `anti-slop` (`postprocess` mode) |
| `ask-chatgpt` | `ask-to-chatgpt` |
| `ask-to-web-gemini` | `ask-to-gemini` |
| `debate-web-models` | `debate-models` (explicit peer/transport declaration) |
| `chatgpt-rubric-evaluator`, `evaluate-with-chatgpt` | `evaluate-with-rubric` |
| `by-subagent` | `orchestrate-agents` (Tier 1) |
| `codex-team-orchestration`, `orchestrate-agent-team` | `orchestrate-agents` (Tier 2) |
| `requirements-interview` | `interview-for-requirements` |
| `teach-socratically` | Upstream [`socratic-tutor`](https://github.com/janestreet/agent_skills/blob/master/socratic-tutor/SKILL.md) (linked upstream, not packaged locally) |
| `implementation-workflow-orchestrator` | `sdd-00-orchestrate-implementation` |
| `repository-implementation-planner` | `sdd-01-plan-repository-implementation` |
| `implementation-spec-assessor` | `sdd-02-assess-implementation-spec` |
| `implementation-plan-executor` | `sdd-03-execute-implementation-plan` |
| `independent-workflow-verifier` | `sdd-04-verify-implementation-independently` |
| `release-readiness-assessor` | `sdd-05-assess-release-readiness` |

SDD `00` is the entry point; `02` assesses both specifications and plans. Numbers show a common order, not mandatory steps for every task.

### Skill harness and routing guardrails

Every packaged skill enforces explicit activation boundaries and pre-flight gates so agents invoke the right tool without burning local tokens unnecessarily or crossing role boundaries:

| Skill | Use when | Do NOT use when | Mandatory pre-flight guardrail |
| --- | --- | --- | --- |
| `anti-slop` | Drafting EN/KO prose (`draft`) or stripping observable slop from supplied docs (`postprocess`) | Factual rewriting or code review | Declare `draft` vs `postprocess`; never save cover letters to disk; run `check_slop.py --strict` |
| `ask-to-chatgpt` | Single-shot Web ChatGPT query via Aside CLI | Multi-round debate (`debate-models`) or rubric scoring (`evaluate-with-rubric`) | Confirm Aside CLI, login, and highest reasoning before sending; never substitute models silently |
| `ask-to-gemini` | Single-shot Web Gemini (`Neon High`) query via Aside CLI | Multi-round debate (`debate-models`) or rubric scoring (`evaluate-with-rubric`) | Confirm Aside CLI, login, Chat mode, and `Neon` + `High` before sending; use Quill-safe `insertText` |
| `debate-models` | High-stakes decision needing 2-node ACH falsification (up to 3 rounds) | Single-shot lookup (`ask-to-*`) or rubric scoring (`evaluate-with-rubric`) | Explicitly declare Peer A, Peer B, and transport (`web-pair` vs `local-pair` vs `hybrid-pair`) before Round 1 |
| `evaluate-with-rubric` | Reproducible weighted rubric scoring of a file or directory | Unstructured Q&A (`ask-to-*`) or open-ended debate (`debate-models`) | Pass deterministic checks first; declare critic backend; inspect packet before sharing; validate JSON locally |
| `orchestrate-agents` | Bounded parallel workers (Tier 1) or multi-team delivery (Tier 2) | Short, single-file, or tightly sequential work | Declare Tier 1 vs Tier 2; enforce one writer per file; require JSON contracts and frozen-revision review |
| `interview-for-requirements` | Unclear goals, flows, constraints, acceptance criteria, or hidden system context | Requirements are already clear, or structured tutoring (`socratic-tutor`) | Inspect system facts read-only first; enforce 5-label provenance (`OBSERVED_FACT` separate from `R-NN`) and Slice 1 IDs before `sdd-01`/`sdd-02` |
| `sdlc-stage-rubrics` | Risk-tiered (T1-T3) 4-stage SDLC scoring and gating | Generic non-SDLC rubrics | Run `evaluate_sdlc_gate.py` for T2/T3 thresholds, critical floors, and human sign-off |
| `sdd-00`..`sdd-05` | Formal Spec-Driven Development from plan through release readiness | Small direct edits that do not need formal gates | Keep planning read-only; require `READY` Spec/Plan Gates + explicit approval before execution; freeze candidate before independent verification |

## Requirements

The Planner, Executor, Orchestrator, Independent Workflow Verifier, and Release Readiness Assessor use Markdown instructions. The Assessor's scripts and tests require Python 3.11 or newer. The `evaluate-with-rubric` scripts require Python 3.10 or newer and use the standard library. Install the Assessor and repository test dependencies in an isolated environment:

```sh
python3.11 -m venv .venv
. .venv/bin/activate
python -m pip install -r skills/spec-driven-development/02-assessment/sdd-02-assess-implementation-spec/requirements.txt
```

## Contributing

1. Check the catalog for an existing skill that covers the proposed task.
2. Read [AGENTS.md](AGENTS.md) for admission criteria, package rules, and required checks.
3. Make the change under `skills/`, update affected catalog and validator entries, and run the checks.
4. Open a pull request describing the use case and the checks you ran.

Run the Assessor's report validator from its folder:

```sh
cd skills/spec-driven-development/02-assessment/sdd-02-assess-implementation-spec
python scripts/validate_assessment.py --report tests/fixtures/reports/excellent.json --source tests/fixtures/excellent-prompt.md
```

The manual release scenario is in `skills/spec-driven-development/05-release-readiness/sdd-05-assess-release-readiness/scenarios/`. Do not treat it as an automated test or claim it ran without recorded evidence.

## License

MIT. See [LICENSE](LICENSE).
