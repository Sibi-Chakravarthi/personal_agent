# Agent Collaboration: Creative UI Pipeline

Goal: Enable Panda to instantly scaffold beautiful, multi-file websites and applications using a hybrid pipeline: DeepSeek-R1 (planning) -> Qwen2.5-Coder (execution) via [write_files_batch](file:///d:/personal_agent/personal_agent/tools/project_builder.py#9-48). Additionally, replace the brittle keyword-based routing with a reliable LLM-based intent classifier using a very small, fast model (`llama3.2:1b`).

## User Review Required
The user has requested renaming the agent to Panda, merging the DeepSeek pipeline with the new project builder tools, and using an LLM to route prompts.

## Proposed Changes

### 1. [config.py](file:///d:/personal_agent/personal_agent/config.py) & Agent Renaming
- Set `MODELS["router"] = "llama3.2:1b"` to act as the fast classification model.
- Rename JARVIS to Panda across [main.py](file:///d:/personal_agent/personal_agent/main.py) and [agent.py](file:///tmp/test_agent.py).

### 2. [router.py](file:///d:/personal_agent/personal_agent/router.py) (LLM-Based Routing)
- Completely replace `CODE_KEYWORDS` and `REASONING_KEYWORDS` dictionaries.
- Update [pick_model(user_message)](file:///d:/personal_agent/personal_agent/router.py#46-67) to send a zero-shot classification prompt to the `router` model.
- The prompt will force the model to output exactly one word: `CODE`, `REASONING`, or `GENERAL`. It will route frontend/website/complex logic to `REASONING` (DeepSeek) and raw programming to `CODE` (Qwen).

### 3. [agent.py](file:///tmp/test_agent.py) (DeepSeek -> Qwen Pipeline)
- **Tool Registry**: Add `delegate_to_coder` back to `TOOLS`. When called, it spawns a sub-agent strictly using `MODELS["code"]` (`qwen2.5-coder:14b`).
- **Project Builder Integration**: Ensure [write_files_batch](file:///d:/personal_agent/personal_agent/tools/project_builder.py#9-48) remains intact so Qwen can dump the entire frontend codebase in one tool execution.
- **System Prompt**: 
  - Mandate aesthetic UI/UX (glassmorphism, animations, gradients).
  - Explicitly restrict DeepSeek: "Do NOT use [write_files_batch](file:///d:/personal_agent/personal_agent/tools/project_builder.py#9-48) yourself. Output a detailed architecture spec to `delegate_to_coder` instead."
  - Explicitly restrict Qwen (in Sub-Agent mode): "Use [write_files_batch](file:///d:/personal_agent/personal_agent/tools/project_builder.py#9-48) to write this spec to disk."

## Verification
- Run [test_builder.py](file:///d:/personal_agent/personal_agent/test_builder.py) and [test_collaboration.py](file:///d:/personal_agent/personal_agent/test_collaboration.py) to ensure the router correctly identifies intents and the hybrid pipeline works cleanly.
