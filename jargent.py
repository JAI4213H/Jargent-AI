
from langchain_core.tools import tool
from langchain_core.utils.function_calling import convert_to_openai_tool
from openai import OpenAI
import os
import time as t
import subprocess
import json
import voice_functions as vf
from datetime import datetime
import jargentfunctions as jf

memory = jf.load_memory()
print("Memory Loaded Sucessfully")

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
        api_key = "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"
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
    if v_userinput is not None and v_userinput.strip():
        
        inp = v_userinput
        memory.append({"role": "user","content": fr"{inp}"})
    else:
        inp = str(input("Enter Promot: "))
        memory.append({"role": "user","content": fr"{inp}"})
    
    
    if (v_userinput or "").lower().strip(". ") == "exit" or (inp or "").lower().strip(". ") == "exit":
        jf.exit(memory=memory)
        
        break
    while True:
        print("SENT REQ TO BACKEND")
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
