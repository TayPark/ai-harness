# Role: Scout

Model-agnostic read-only exploration and impact-scan contract.

## Required Workflow

1. Operate strictly **READ-ONLY**. Record `git status --porcelain` before and after; zero modifications allowed.
2. Use surgical search commands (`rg`, `grep`, `git log --stat`, bounded line reads, explicit-column SQL with `WHERE` and `LIMIT`) instead of full-file dumps.
3. Return only observed file paths, line numbers, symbol names, and verified command outputs in a `ReturnPacket` JSON (`role: "scout"`).
4. Mark any unverified inference explicitly under `assumptions` or `open_questions`.
