"""Gemini tool-using agent with three prompt configurations."""
from __future__ import annotations
import json, time
from google import genai
from google.genai import types
from .tools import TOOL_SCHEMAS, run_tool

CONFIGS = {
    "baseline": "You are a helpful assistant. Solve the task and use tools when needed.",
    "structured": ("You are a careful task-execution agent. Identify the required operation, "
                   "call the most relevant tool with exact arguments, then report only verified results."),
    "verify": ("You are a reliable agent. Use the appropriate tool, inspect its returned data, "
               "check that it answers the request, and correct mistakes with another tool call if needed. "
               "Never invent tool results."),
}

def run_agent(prompt: str, config_name: str, model: str, api_key: str, max_steps: int = 5):
    if config_name not in CONFIGS:
        raise ValueError(f"Unknown config: {config_name}")
    client = genai.Client(api_key=api_key)
    declarations = [types.FunctionDeclaration(
        name=s["name"], description=s["description"], parameters=s["parameters"]
    ) for s in TOOL_SCHEMAS]
    tool = types.Tool(function_declarations=declarations)
    cfg = types.GenerateContentConfig(
        system_instruction=CONFIGS[config_name],
        tools=[tool],
        temperature=0,
    )
    contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]
    logs, tool_errors, final_text = [], 0, ""
    start = time.perf_counter()
    for step in range(max_steps):
        response = client.models.generate_content(model=model, contents=contents, config=cfg)
        candidate = response.candidates[0]
        model_content = candidate.content
        contents.append(model_content)
        calls = [p.function_call for p in model_content.parts if p.function_call]
        if not calls:
            final_text = response.text or ""
            break
        response_parts = []
        for call in calls:
            args = dict(call.args or {})
            entry = {"step": step + 1, "tool": call.name, "arguments": args}
            try:
                result = run_tool(call.name, args)
                entry.update({"ok": True, "result": result})
            except Exception as exc:
                tool_errors += 1
                result = {"error": str(exc)}
                entry.update({"ok": False, "error": str(exc)})
            logs.append(entry)
            response_parts.append(types.Part.from_function_response(
                name=call.name, response={"result": result}
            ))
        contents.append(types.Content(role="tool", parts=response_parts))
    latency = time.perf_counter() - start
    return {"final_text": final_text, "tool_logs": logs, "tool_errors": tool_errors,
            "tool_calls": len(logs), "latency_seconds": latency}
