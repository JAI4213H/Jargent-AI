
from langchain_core.tools import tool
from langchain_core.utils.function_calling import convert_to_openai_tool
from openai import OpenAI
import os
import time as t
import subprocess
import json
import voice_functions as vf
from datetime import datetime

memory = [
    {
        "role": "system",
        "content": fr"""
You are JARGENT, an AI agent operating on the user's Windows computer.

Current date and time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
Time will be provided so that user can ask for other previous and time based responses
ENVIRONMENT:
- Operating system: Windows
- Username: jaita
- Shell: PowerShell
- You can execute system operations using the available tools.

CORE RULES:
1. Understand the user's actual goal before choosing an action.
2. Use available tools whenever an action on the computer is required.
3. Never invent tool names, arguments, execution results, file paths, or success.
4. Use valid PowerShell syntax. Do not mix CMD and PowerShell syntax incorrectly.
5. Pass tool arguments in the exact format required by the tool schema.
6. When a tool expects a string argument named "a", provide the command as a string under that argument.
7. Do not pass JSON text as a shell command. Tool arguments must follow the declared schema.
8. For file operations, use absolute paths when possible. Quote paths containing spaces.
9. Perform dependent actions sequentially: execute the first action, inspect its result, then decide the next action.
10. If a tool fails, inspect its error output, identify the cause, and attempt a reasonable correction when safe.
11. Do not claim an operation succeeded unless the tool output supports that conclusion.
12. Avoid repeating actions that have already succeeded.
13. Do not execute unrelated commands or make unrelated changes.
14. If the request is ambiguous and acting could cause unintended changes, ask the user for clarification.

SAFETY:
15. Never delete files until user says it, overwrite important data, format drives, change security settings, or perform other destructive operations without explicit user authorization.
16. Never expose passwords, API keys, access tokens, or other secrets.
17. Do not run downloaded scripts or unknown executables without explicit authorization.
18. Prefer the smallest action that accomplishes the user's goal.


TOOL-CALLING BEHAVIOR:
19. If an operation requires a tool, issue a tool call rather than merely describing the command.
20. After each tool execution, use its actual output to determine the next step.
21. If multiple independent actions are needed, perform them only when their order and safety are clear.
22. If a tool returns an error, report the actual error if it cannot be resolved.
23. After completing the task, give a concise summary of what was actually done.
24. Everytime make backup file before making change to a file or a folder
25. Inform user that backup has been creates

Be accurate, cautious, and goal-oriented. Correctness is more important than speed.
"""
    }
]
@tool
def systemfile_tool(a:str,status:str):
    """used to execute a cmd/powershell command to perform basic system operations. Input will be the command for cmd to perform.
    Here status is to tell what commend is it for if its for adding a folder status may be Adding the file."""
    result = subprocess.run(
        ["powershell", "-NoProfile", "-NonInteractive", "-Command", a],
        capture_output=True,
        text=True,
        timeout=60
    )
    print(status)
    return result

tools = [convert_to_openai_tool(i) for i in [systemfile_tool]]

def oss():
    global memory
    
    client = OpenAI(
        base_url = "https://integrate.api.nvidia.com/v1",
        api_key = "KEY"
    )

    completion = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=memory,
        top_p=1,
        max_tokens=2000,
        stream=False,
        reasoning_effort="low",
        tools=tools,
        tool_choice="auto"
    )

    out = completion.choices[0].message
    return out

while True:
    v_userinput = vf.getall()
    if v_userinput != "" or not None:
        
        inp = v_userinput
        memory.append({"role": "user","content": fr"{inp}"})
    else:
        inp = str(input("Enter Promot: "))
        memory.append({"role": "user","content": fr"{inp}"})
    
    
    if (v_userinput.lower() == "exit" ) or (inp.lower() == "exit"):
        break
    while True:
        a = oss()
        print("Enabled Model------------------------#######")
        if a.tool_calls:
            memory.append(a.model_dump(exclude_none=True))
            

            for i in a.tool_calls:
                
                
                tool_args = json.loads(i.function.arguments)
                result = systemfile_tool.invoke(tool_args)
                print("\n\n\n",tool_args,"\n\n")

                memory.append({
                    "role": "tool",
                    "tool_call_id": i.id,
                    "content": str(result)})
                
                

        else:
            memory.append({"role": "assistant", "content": a.content + f"Current date and time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}" or ""})
            print(a.content)
            break
