from __future__ import annotations


def build_agent_task_state(agent_type: str, artifacts: list[str]) -> dict[str, object]:
    tasks = [
        {
            "id": f"{agent_type}:{artifact}",
            "agent_type": agent_type,
            "artifact": artifact,
            "title": f"Produire {artifact}",
            "status": "pending",
            "order": index + 1,
        }
        for index, artifact in enumerate(artifacts)
    ]
    return summarize_task_state(
        {
            "schema_version": "claude_agent_task_state_v0",
            "agent_type": agent_type,
            "tasks": tasks,
            "current_task_id": "",
        }
    )


def update_task_status(task_state: dict[str, object], artifact: str, status: str) -> dict[str, object]:
    tasks = task_state.get("tasks", [])
    if not isinstance(tasks, list):
        tasks = []
    current_task_id = ""
    for task in tasks:
        if not isinstance(task, dict):
            continue
        if task.get("artifact") == artifact:
            task["status"] = status
            current_task_id = str(task.get("id") or "")
            break
    task_state["current_task_id"] = current_task_id if status == "in_progress" else ""
    return summarize_task_state(task_state)


def summarize_task_state(task_state: dict[str, object]) -> dict[str, object]:
    tasks = task_state.get("tasks", [])
    if not isinstance(tasks, list):
        tasks = []
    status_counts = {"pending": 0, "in_progress": 0, "completed": 0, "blocked": 0}
    for task in tasks:
        if not isinstance(task, dict):
            continue
        status = str(task.get("status") or "pending")
        status_counts[status] = status_counts.get(status, 0) + 1
    task_state["tasks_count"] = len(tasks)
    task_state["pending_count"] = status_counts.get("pending", 0)
    task_state["in_progress_count"] = status_counts.get("in_progress", 0)
    task_state["completed_count"] = status_counts.get("completed", 0)
    task_state["blocked_count"] = status_counts.get("blocked", 0)
    task_state["ok"] = bool(tasks) and task_state["completed_count"] == len(tasks) and task_state["blocked_count"] == 0
    return task_state


def summarize_pipeline_task_states(task_states: dict[str, dict[str, object]]) -> dict[str, object]:
    totals = {
        "tasks_count": 0,
        "pending_count": 0,
        "in_progress_count": 0,
        "completed_count": 0,
        "blocked_count": 0,
    }
    for task_state in task_states.values():
        for field_name in totals:
            totals[field_name] += int(task_state.get(field_name, 0) or 0)
    return {
        "schema_version": "claude_pipeline_task_summary_v0",
        "agent_type": "claude-pipeline",
        "agents_count": len(task_states),
        **totals,
        "ok": totals["tasks_count"] > 0 and totals["completed_count"] == totals["tasks_count"] and totals["blocked_count"] == 0,
    }
