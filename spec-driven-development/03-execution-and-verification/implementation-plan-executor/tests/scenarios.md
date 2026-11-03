# Manual behavior scenarios

## Failed prerequisite blocks dependent work

Given phase B depends on phase A, when A fails, record A as `failed` with its exact command, exit result, and evidence path. Mark B `blocked` and do not start it. Preserve partial work from A. Record the next safe action.

## Missing phase owner

Given the plan does not name an owner for phase A, record the owner as `unassigned`. Do not infer a person or role. Continue only when the phase's approval and dependency gates pass.

## Missing approval

Given a plan has no explicit approval evidence, stop before edits or state-changing commands. Report the missing evidence and request approval. Read-only inspection may identify the plan version and proposed scope.
