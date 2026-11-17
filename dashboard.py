from pathlib import Path
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

st.set_page_config(page_title="Agentic AI Evaluation", layout="wide")
st.title("Agentic AI Evaluation Dashboard")
st.caption("Compare task completion, tool reliability, and latency. Dry-run results are plumbing checks, not LLM scores.")
root = Path(__file__).parent / "results"
choices = list(root.glob("task_results_*.csv"))
uploaded = st.file_uploader("Or upload a task results CSV", type="csv")
if uploaded:
    df = pd.read_csv(uploaded)
elif choices:
    selected = st.selectbox("Choose results file", choices, format_func=lambda p: p.name)
    df = pd.read_csv(selected)
else:
    st.info("No results yet. Run the experiment script to create a CSV.")
    st.stop()

if df.empty:
    st.warning("The selected file has no rows.")
    st.stop()

if "task_completed" in df.columns:
    df["task_completed"] = df["task_completed"].fillna(False).astype(bool)
else:
    st.error("The results CSV is missing the 'task_completed' column.")
    st.write("Available columns:", df.columns.tolist())
    st.stop()
summary = df.groupby("config").agg(
    Tasks=("task_id","count"),
    Completion=("task_completed","mean"),
    Tool_Errors=("tool_errors","sum"),
    Tool_Calls=("tool_calls","sum"),
    Mean_Latency=("latency_seconds","mean")
).reset_index()
summary["Completion (%)"] = (summary.pop("Completion") * 100).round(1)
summary["Mean latency (s)"] = summary.pop("Mean_Latency").round(3)
summary["Tool error rate (%)"] = (100 * summary["Tool_Errors"] / summary["Tool_Calls"].clip(lower=1)).round(1)
st.subheader("Configuration summary")
st.dataframe(summary, use_container_width=True, hide_index=True)
c1,c2,c3 = st.columns(3)
c1.metric("Rows evaluated", len(df))
c2.metric("Overall completion", f"{100*df.task_completed.mean():.1f}%")
c3.metric("Mean latency", f"{df.latency_seconds.mean():.3f}s")

st.subheader("Task completion by configuration")
fig, ax = plt.subplots()
(df.groupby("config")["task_completed"].mean()*100).plot(kind="bar", ax=ax)
ax.set_ylabel("Completion (%)"); ax.set_ylim(0,100); ax.set_xlabel("Configuration")
st.pyplot(fig); plt.close(fig)

st.subheader("Latency by configuration")
fig, ax = plt.subplots()
df.boxplot(column="latency_seconds", by="config", ax=ax)
ax.set_title(""); ax.set_xlabel("Configuration"); ax.set_ylabel("Latency (seconds)")
st.pyplot(fig); plt.close(fig)

st.subheader("Individual task outcomes")
st.dataframe(df, use_container_width=True, hide_index=True)
st.download_button("Download filtered results CSV", df.to_csv(index=False),
                   file_name="agent_evaluation_results.csv", mime="text/csv")
