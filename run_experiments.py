from __future__ import annotations
import argparse, csv, json, os, time
from pathlib import Path
from dotenv import load_dotenv
from agent_eval.benchmark import TASKS
from agent_eval.agent import run_agent
from agent_eval.tools import run_tool
from agent_eval.metrics import verify, summarize

ROOT = Path(__file__).parent
RESULTS = ROOT / "results"
RESULTS.mkdir(exist_ok=True)

def dry_run(task, config):
    """Offline plumbing check: directly invokes the expected tool; NOT an agent score."""
    start = time.perf_counter()
    result = run_tool(task["tool"], task["args"])
    latency = time.perf_counter() - start
    ok, actual, expected = verify(task, result)
    log = [{"step": 1, "tool": task["tool"], "arguments": task["args"],
            "ok": True, "result": result, "mode": "dry_run"}]
    return {"final_text": "OFFLINE DRY RUN - expected tool invoked directly.",
            "tool_logs": log, "tool_errors": 0, "tool_calls": 1,
            "latency_seconds": latency, "task_completed": ok,
            "verified_value": actual, "expected_value": expected}

def main():
    parser = argparse.ArgumentParser(description="Run the Agentic AI benchmark.")
    parser.add_argument("--runs", type=int, default=1, help="Repeated runs per configuration")
    parser.add_argument("--configs", nargs="+", default=["baseline","structured","verify"])
    parser.add_argument("--dry-run", action="store_true", help="Offline tool plumbing check; not an LLM evaluation")
    args = parser.parse_args()
    if args.runs < 1:
        parser.error("--runs must be at least 1")
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    if not args.dry_run and not api_key:
        raise SystemExit("Missing GEMINI_API_KEY. Copy .env.example to .env and add your key.")
    rows, logs = [], []
    for config in args.configs:
        for run_no in range(1, args.runs + 1):
            for task in TASKS:
                try:
                    if args.dry_run:
                        outcome = dry_run(task, config)
                    else:
                        outcome = run_agent(task["prompt"], config, model, api_key)
                        # The evaluator checks the first successful matching tool result,
                        # not the model's prose. This makes completion externally verifiable.
                        match = next((x for x in outcome["tool_logs"]
                                      if x.get("tool") == task["tool"] and x.get("ok")), None)
                        ok, actual, expected = verify(task, match["result"]) if match else (False, None, task["check"]["equals"])
                        outcome.update({"task_completed": ok, "verified_value": actual,
                                        "expected_value": expected})
                    row = {"config": config, "run": run_no, "task_id": task["id"],
                           "task_completed": outcome["task_completed"],
                           "tool_calls": outcome["tool_calls"], "tool_errors": outcome["tool_errors"],
                           "latency_seconds": round(outcome["latency_seconds"], 6),
                           "verified_value": str(outcome.get("verified_value")),
                           "expected_value": str(outcome.get("expected_value")),
                           "final_text": outcome["final_text"],
                           "mode": "dry_run" if args.dry_run else "gemini"}
                    rows.append(row)
                    for log in outcome["tool_logs"]:
                        logs.append({"config":config,"run":run_no,"task_id":task["id"],**log})
                    print(f'{config} run {run_no} {task["id"]}: '
                          f'{"PASS" if row["task_completed"] else "FAIL"}')
                except Exception as exc:
                    rows.append({"config":config,"run":run_no,"task_id":task["id"],
                                 "task_completed":False,"tool_calls":0,"tool_errors":1,
                                 "latency_seconds":0,"verified_value":"None",
                                 "expected_value":str(task["check"]["equals"]),
                                 "final_text":f"ERROR: {exc}",
                                 "mode":"dry_run" if args.dry_run else "gemini"})
                    print(f'{config} run {run_no} {task["id"]}: ERROR {exc}')
    suffix = "dry_run" if args.dry_run else "gemini"
    csv_path = RESULTS / f"task_results_{suffix}.csv"
    log_path = RESULTS / f"tool_logs_{suffix}.jsonl"
    if rows:
        with csv_path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=list(rows[0]))
            writer.writeheader(); writer.writerows(rows)
    with log_path.open("w", encoding="utf-8") as f:
        for item in logs: f.write(json.dumps(item, ensure_ascii=False) + "\n")
    print("\nSUMMARY")
    for config in args.configs:
        subset = [r for r in rows if r["config"] == config]
        print(config, summarize(subset))
    print(f"\nSaved: {csv_path}\nSaved: {log_path}")

if __name__ == "__main__":
    main()
