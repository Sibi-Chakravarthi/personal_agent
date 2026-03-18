from agent import run_agent

history = []
user_input = "can you code a website with interactive scrolling display of an f1 car create the directory and save the files in D:\\Testing\\F1TestDeepseek"

print("--- Starting Agent Workflow ---\n")
try:
    final_answer, new_history = run_agent(user_input, history, verbose=True)
    print(f"\n✅ FINAL SYSTEM OUTCOME:\n{final_answer}\n")
except Exception as e:
    import traceback
    traceback.print_exc()
