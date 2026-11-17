# Agentic AI Evaluation — Python + Gemini

This is a runnable practical project, **not an article/report**. It benchmarks an LLM agent on 20 predefined tasks and evaluates actions using independent tool-output checks rather than judging only the final written answer.

## Included

- Gemini API integration (`google-genai`)
- 20 controlled benchmark tasks in `agent_eval/benchmark.py`
- Five deterministic mock tools: calculator, order lookup, catalog search, unit conversion, and note saving
- Three prompt configurations: `baseline`, `structured`, and `verify`
- Task completion, tool error rate, average/median latency, and average tool calls
- Per-task CSV results and JSONL tool execution logs
- Streamlit dashboard with comparison graphs and CSV export
- Offline `--dry-run` to check that the benchmark and tools work without an API key

## Architecture

```text
Benchmark task set
       |
       v
Task/configuration runner
       |
       v
Gemini agent  <------>  Tool functions
       |                    |
       |                    v
       |               Tool execution log
       v
Final response
       |
       v
Independent outcome verifier <---- expected benchmark result
       |
       v
Metrics + CSV/JSONL -----> Streamlit dashboard
```

## Setup (Windows PowerShell)

1. Install Python 3.10 or newer.
2. Extract the ZIP and open the project folder in VS Code.
3. Create and activate a virtual environment:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
```

4. Install packages:

```powershell
pip install -r requirements.txt
```

5. Copy `.env.example` to `.env` and add your Gemini API key:

```text
GEMINI_API_KEY=your_actual_key
GEMINI_MODEL=gemini-2.5-flash
```

Keep `.env` private. Never upload it to GitHub or share the API key.

## Run an offline plumbing check

```powershell
python run_experiments.py --dry-run
```

This calls each expected tool directly and checks the benchmark verifier. It confirms that the tools, tasks, and result pipeline work. **It does not evaluate an LLM** and must not be reported as an agent experiment.

## Run the Gemini experiment

```powershell
python run_experiments.py
```

This runs all 20 tasks once for each of the three configurations (60 task executions). For a repeated experiment:

```powershell
python run_experiments.py --runs 3
```

To compare only two configurations:

```powershell
python run_experiments.py --configs baseline verify --runs 2
```

API usage and cost depend on model/provider pricing and may vary. Start with one run before increasing repetitions.

## Open the dashboard

After a run creates a CSV:

```powershell
streamlit run dashboard.py
```

The dashboard displays configuration summaries, completion, tool errors, latency, task-level outcomes, graphs, and a CSV download.

## Metrics

- **Task completion rate** = independently verified completed tasks / total tasks × 100.
- **Tool error rate** = failed tool invocations / total tool invocations × 100.
- **Latency** = wall-clock time from the first model request until the agent stops, including tool calls.
- **Average tool calls** = total tool calls / tasks.
- **Median latency** is also reported to reduce the influence of unusually slow requests.

A task is completed only when the expected tool is called successfully and its returned data contains the expected value. The final prose is retained for inspection but is not used as the completion score.

## Files generated

- `results/task_results_gemini.csv`
- `results/tool_logs_gemini.jsonl`
- `results/task_results_dry_run.csv`
- `results/tool_logs_dry_run.jsonl`

The results folder starts empty. Actual experiment tables and graphs are generated after you run the project with your own API key.

## Fairness, validity, and limitations

1. The benchmark is small and uses deterministic mock tools; it does not represent all real-world agent work.
2. The tasks are mostly single-tool tasks. Multi-step planning, long-horizon memory, and complex recovery need a larger benchmark.
3. Prompt configurations are compared while model, task set, temperature, and tool definitions are held constant. This improves comparability but does not isolate every source of randomness.
4. API latency can vary with network conditions, provider load, and rate limits. Repeat runs and report mean/median plus the run count.
5. Tool outputs are deterministic, but model tool selection and argument generation can vary.
6. The verifier checks exact expected values. This is reproducible but may mark semantically correct alternative responses as failures.
7. The `verify` configuration is a prompt strategy, not a guarantee of correctness.
8. Do not compare configurations using different task subsets or undisclosed model settings.

## Suggested experiment procedure

1. Run `--dry-run` once to validate local setup.
2. Run the Gemini experiment once for all configurations.
3. Repeat at least three times if API quota and time permit.
4. Compare completion rate, tool error rate, and latency together. A faster agent is not necessarily more reliable.
5. Inspect failed rows and matching JSONL tool logs before drawing conclusions.
6. In your practical write-up, report the model name, date, run count, configuration prompts, and any API errors.

## Troubleshooting

- `Missing GEMINI_API_KEY`: copy `.env.example` to `.env` and add a valid key.
- `ModuleNotFoundError`: activate the virtual environment and run `pip install -r requirements.txt`.
- API errors: check the key, API access, model availability, quota, and internet connection.
- No dashboard results: run the experiment first, or upload a compatible results CSV.
