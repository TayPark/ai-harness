# Guardrails

## Default Read-Only Posture

Operate **READ-ONLY** by default. Do not mutate files, databases, git history, or external state unless one of the following holds:

1. The user explicitly requested the mutation in the current session, or
2. An approved implementation plan explicitly covers that mutation.

Never infer or assume consent for state-changing or destructive operations.

## Explicit Consent Gate for Mutating and Destructive Commands

Stop and request explicit user confirmation before executing any command that creates, inserts, updates, or deletes persistent state outside an already-approved scope:

- Database / Data: `CREATE`, `INSERT`, `UPDATE`, `DELETE`, `DROP`, `ALTER`, `TRUNCATE`, schema migrations, or bulk backfills.
- External APIs / Infra: `POST`, `PUT`, `PATCH`, `DELETE`, deployments, billing changes, or cloud mutations (`kubectl`, `terraform apply/destroy`, `aws`, `gcloud`).
- Filesystem / Git: `rm`, destructive `mv` overwrite, `git push`, `git reset --hard`, `git branch -D`, `gh pr merge`, or direct commits/pushes to `main`, `master`, or `release`.

## Deterministic Fast-Path Exception

Direct single-agent edits without multi-agent orchestration are permitted only when **all** conditions hold:

1. The user explicitly authorized the edit.
2. Total diff is `<=30` lines across `<=2` files.
3. No schema, security, permission, or infrastructure changes are involved.
4. For code repositories, work happens inside a feature branch or worktree (unless the user explicitly authorized the current branch).

## Secret and Privacy Hygiene

- Never print, commit, or transmit `.env*`, `*.pem`, `*.key`, `id_rsa`, `id_ed25519`, `~/.ssh/**`, cloud credentials, or OAuth tokens.
- Never commit personal home directory paths into public repositories.

## Verification Integrity

- Never delete failing assertions, add unjustified `@ts-ignore` or test skips, or fabricate command outputs.
- If a check cannot run, state the exact reason and mark the status `미확인` or `BLOCKED`.
