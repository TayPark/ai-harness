---
name: by-subagent
description: Delegate independent work while limiting the orchestrator's context. Use when workers should load their own specialist skills or retrieve task-specific evidence, and for bounded research, analysis, or staged implementation.
---

# by-subagent

Use subagents for bounded work that benefits from independent execution. Keep simple, short, dependent, or same-file work with the main agent unless the user requests otherwise.

Keep the orchestrator's context to decomposition, task boundaries, integration, and final verification. Do not read a worker's specialist skill or broad RAG material only to copy it into the handoff. Give the worker precise paths and let it read the applicable instructions and retrieve evidence for its task.

Skill names and descriptions support discovery. They do not enforce context isolation, file access, or tool permissions. Use host-level controls when access must be restricted. A narrow prompt is not a security boundary.

## Workflow

1. Split the request into small tasks with clear boundaries. Run tasks in parallel only when they do not depend on each other's results. Run dependent tasks in order.
2. Give each task its own ID, objective, permitted inputs and tools, constraints, required reading, and expected result. Assign one writer per target file.
3. Start a fresh worker context when the host supports it. Pass the task contract and essential identifiers, not the full conversation, unrelated skills, or broad RAG results.
4. Tell the worker which skills and source paths apply. Let it read those instructions and retrieve task evidence. Ask it to identify the sources and revisions it used.
5. Ask each subagent to return one JSON object using the response contract below. For a dependent task, pass the prior task's validated JSON as input; do not replace it with an unverified summary.
6. Parse each response as JSON and inspect it. Confirm its task ID, status, evidence, and limitations. Treat invalid JSON syntax, missing required fields, or a missing prerequisite as incomplete; ask for correction or report the task as incomplete.
7. Check findings against their evidence, resolve conflicts, and synthesize the final answer as the main agent. Do not present an agent's unsupported claim as verified fact.
8. If the host cannot start a fresh context or preserve required inputs and results, pass a concise, validated handoff and record the limitation. If the host has no usable subagent capability, do the work directly when practical. State that delegation did not run.

For independent review, freeze the target and record its revision or hash first. Give reviewers the same target revision and only the references needed for their review lens. Reviewers return findings and do not edit the target. Any edit invalidates reviews tied to the old revision.

## Task request contract

Send each subagent a JSON object with these fields:

```json
{
  "task_id": "stable-task-id",
  "objective": "One bounded task and its expected outcome",
  "inputs": [],
  "constraints": [],
  "required_reading": [],
  "expected_result": "One JSON object matching the response contract"
}
```

Use `inputs` for relevant source material, including the full validated response from a prerequisite task. Limit each subagent to the material and tools needed for its task.

## Response contract

Require one valid JSON object with all fields below. Use `null` or an empty array when a field has no content.

```json
{
  "task_id": "stable-task-id",
  "status": "complete | incomplete | blocked",
  "result": "Concise findings or output",
  "evidence": [],
  "assumptions": [],
  "limitations": [],
  "open_questions": []
}
```

Evidence must identify the supporting file and location, source URL, or observed result. Keep facts separate from assumptions. A `complete` status requires the requested result and its evidence; otherwise use `incomplete` or `blocked`.

## Example

```text
Use $by-subagent: Research [company or ticker]. Collect current price and recent news as separate tasks if both can run independently. Include the observation time and source links. Return each task as JSON, then reconcile the findings in one concise report. If subagents are unavailable, say so and do not claim parallel research.
```
