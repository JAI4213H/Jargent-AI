
import os
import base64
from openai import OpenAI
import subprocess
from langchain_core.tools import tool
from langchain_core.utils.function_calling import convert_to_openai_tool
from PIL import ImageGrab
import uuid


client = OpenAI(
    api_key=os.environ["GROQ_API_KEY"],
    base_url="https://api.groq.com/openai/v1"
)
@tool
def vision(file_name, prompt="Describe this image."):
    """Use this tool to analyze an image or screenshot and answer
    the user's questions about its contents. It can identify UI elements,
    read visible text, describe objects, and extract relevant visual details."""
    with open(file_name, "rb") as f:
        image = base64.b64encode(f.read()).decode("utf-8")

    response = client.chat.completions.create(
        model="qwen/qwen3.8-27b",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{image}"
                        }
                    }
                ]
            }
        ]
    )

    return response.choices[0].message.content

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


@tool
def take_screenshot():
    """Capture the current screen and save it as a uniquely named PNG image."""
    screenshot = ImageGrab.grab()
    name = f"{uuid.uuid4().hex}.png"
    screenshot.save(name)
    return name



tool = [vision,systemfile_tool,take_screenshot]

def get_tools():
    global tool
    tools = [convert_to_openai_tool(i) for i in tool]
    tool_dir = {i.name:i for i in tool}
    return tools,tool_dir


