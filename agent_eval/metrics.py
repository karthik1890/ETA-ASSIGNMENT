from __future__ import annotations
import math

def get_path(data, path):
    for part in path.split("."):
        if not isinstance(data, dict) or part not in data:
            return None
        data = data[part]
    return data

def verify(task, tool_result):
    actual = get_path(tool_result, task["check"]["path"])
    expected = task["check"]["equals"]
    return actual == expected, actual, expected

def summarize(rows):
    n = len(rows)
    if not n:
        return {}
    completed = sum(bool(r["task_completed"]) for r in rows)
    tool_calls = sum(int(r["tool_calls"]) for r in rows)
    tool_errors = sum(int(r["tool_errors"]) for r in rows)
    latencies = [float(r["latency_seconds"]) for r in rows]
    return {
        "tasks": n,
        "completion_rate_pct": round(100 * completed / n, 2),
        "tool_error_rate_pct": round(100 * tool_errors / max(tool_calls, 1), 2),
        "avg_latency_seconds": round(sum(latencies) / n, 3),
        "median_latency_seconds": round(sorted(latencies)[n // 2], 3),
        "avg_tool_calls": round(tool_calls / n, 2),
    }
