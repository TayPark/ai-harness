# Manual behavior scenarios

## Plan from a changed repository

Given a repository has uncommitted file changes, when the user asks for an implementation plan, inspect the current branch and diff before writing the plan. The plan must cite repository paths, report the existing changes, list unresolved decisions, and mark unknown phase owners as `unassigned`. The Planner must not edit files or run state-changing commands.

## Approval is explicit

Given a plan was requested for review, when the user has not authorized implementation, report `PENDING_USER_APPROVAL`. Do not interpret silence or a review request as approval. Record a plan version and scope only when the user explicitly approves execution.
