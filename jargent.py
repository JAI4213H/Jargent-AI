
import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
import jargentfunctions as jf
from groq import Groq
from jargenttools import get_tools, clean_tool_name
from voice_functions import getall, tovoice, wait_for_wake_word

MAX_CONTEXT_MESSAGES = 12

memory = jf.load_memory()
print("Memory Loaded Sucessfully")

tools,tools_dir = get_tools()
print("available tools ", tools_dir.keys())

groq_client = Groq()


def compact_result(result, limit=1000):
    """Keep tool output small before sending it back to the model."""
    if isinstance(result, (dict, list)):
        text = json.dumps(result, ensure_ascii=False, default=str)
    else:
        text = str(result)

    if len(text) > limit:
        return text[:limit] + "\n...[result truncated]"

    return text


def model_memory():
    """Keep the system prompt and only the most recent conversation turns."""
    if len(memory) <= MAX_CONTEXT_MESSAGES:
        return memory
    return memory[:1] + memory[-(MAX_CONTEXT_MESSAGES - 1):]

#fast
def groqmodel():
    completion = groq_client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=model_memory(),
        temperature=0.2,
        max_completion_tokens=600,
        top_p=1,
        reasoning_effort="low",
        stream=False,
        stop=None,
        tools=tools,
        tool_choice="auto",
        disable_tool_validation=True
        
    )
    return completion.choices[0].message






while True:

    print("Recording is ON")
    vc_input = getall()
    
    if vc_input is None:
        print("No Speech Detected")
        inp = str(input("Enter Promot: "))
    
    else:
        inp = vc_input
        
    if inp.lower() == "exit.":
        jf.exit(memory)
        break
        
    memory.append({"role": "user","content": fr"{inp}"})
    

    while True:
        
        a = groqmodel()
        print("SENT REQ TO BACKEND\n")
        if a.tool_calls:
            memory.append(a.model_dump(exclude_none=True))

            def run_tool(call):
                tool_name = clean_tool_name(call.function.name)
                tool_args = json.loads(call.function.arguments)
                print("Calling tool", tool_name)
                try:
                    print("\n\n",tool_args["status"],"\n\n")
                except Exception as e:
                    print("Error showing status, ",e)
                    
                tool_function = tools_dir[tool_name]
                if hasattr(tool_function, "invoke"):
                    result = tool_function.invoke(tool_args)
                else:
                    result = tool_function(**tool_args)

                return {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "name": tool_name,
                    "content": compact_result(result),
                }

            with ThreadPoolExecutor(
                max_workers=min(4, len(a.tool_calls))
            ) as executor:
                memory.extend(executor.map(run_tool, a.tool_calls))
                
            print("Tool execution completed, Sending results back to model...")
            

        else:
            answer = a.content or ""
            memory.append({
                "role": "assistant",
                "content": answer + f"\nCurrent date and time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"})
            print(answer)
            try:
                tovoice(answer)
            except Exception as e:
                print("Error generating voice: ", e)
                
            break
