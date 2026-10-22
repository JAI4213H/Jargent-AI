
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
from groq import Groq
from jargenttools import get_tools

memory = jf.load_memory()
print("Memory Loaded Sucessfully")

tools,tools_dir = get_tools()
print("available tools ", tools_dir)

#SLOW
def nimoss():
    global memory
    
    client = OpenAI(
        base_url = "https://integrate.api.nvidia.com/v1",
        api_key = "NVIDIA_API_KEY"
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
#fast
def groqmodel():
    global memory
    client = Groq()
    completion = client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=memory,
        temperature=1,
        max_completion_tokens=1000,
        top_p=1,
        reasoning_effort="medium",
        stream=False,
        stop=None,
        tools=tools,
        tool_choice="auto"
        
    )
    return completion.choices[0].message






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
        a = groqmodel()
        print("Enabled Model------------------------#######")
        if a.tool_calls:
            memory.append(a.model_dump(exclude_none=True))
            

            for i in a.tool_calls:
                
                tool_name = i.function.name
                tool_args = json.loads(i.function.arguments)
                
                result = tools_dir[tool_name].invoke(tool_args)
                print("\n\n\n",tool_args,"\n\n")

                memory.append({
                    "role": "tool",
                    "tool_call_id": i.id,
                    "content": str(result)})
                
                

        else:
            memory.append({"role": "assistant", "content": a.content + f"Current date and time: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}" or ""})
            vf.tovoice(a.content)
            break
