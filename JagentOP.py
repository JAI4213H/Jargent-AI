from ollama import chat
import threading

class JAgents:
    
    
    the_real_content = """
Summarise the following conversation memory carefully and create a compact but information-rich summary that can be used by the model in future conversations.

Your main goal is to preserve all information that may be useful for understanding future user requests or continuing the conversation.

Make sure to preserve:
1. Important facts and information discussed in the conversation.
2. User preferences, requirements, goals, and constraints.
3. Important decisions that were made.
4. Important technical details, code-related information, configurations, or approaches.
5. Names of important projects, models, tools, libraries, datasets, or technologies.
6. Important problems, errors, solutions, and fixes that were discovered.
7. Any ongoing tasks, unfinished work, or plans that may need to be continued later.
8. Important credentials, keys, tokens, usernames, passwords, API keys, or other sensitive authentication information if they were explicitly provided and are necessary for future use.
9. Any other information that would prevent the model from losing important context from the previous conversation.

Do not include unnecessary small talk, repeated information, or information that has no value for future conversations.

Do not invent, assume, or change any information. Only summarize information that is actually present in the memory.

Keep the summary concise enough to fit into the model context, but detailed enough that the model can understand the important history without needing the original conversation.

Do not use special formatting, markdown, bullet symbols, asterisks, or unnecessary special characters. Write the summary as clear plain text.

Here is the memory that needs to be summarized:


"""

    coding_agent_prompt = """You are a Python code generation model.

Your ONLY task is to generate Python code that directly fulfills the user's request.

STRICT RULES:

1. Your response MUST contain only Python code.
2. NEVER provide explanations.
3. NEVER provide descriptions.
4. NEVER provide examples outside the requested code.
5. NEVER provide tutorials or instructions.
6. NEVER provide comments explaining the code unless the user explicitly requests comments inside the code.
7. NEVER use Markdown code fences.
8. NEVER include introductory or concluding text.
9. NEVER ask questions. If the request is ambiguous, make the most reasonable interpretation and write the code.
10. Write ONLY the functionality requested by the user.
11. Do not add unnecessary functionality.
12. Use Python only.
13. Before returning the code, carefully check it for syntax errors, indentation errors, undefined variables, incorrect imports, invalid function or method calls, incorrect arguments, and obvious logical errors.
14. Fix any errors you find before returning the code.
15. Preserve the user's existing code structure, variable names, formatting, and approach when modifying provided code unless a change is necessary to fulfill the request or fix an error.
16. Do not claim that code was executed or tested.
17. Do not output anything other than the final Python code.

OUTPUT REQUIREMENT:

The response must always be valid Python code and nothing else.
"""

    def __init__(self,chatm:str,summ:str,memory:list,summarising=False):
        self.chatm = chatm #ChaT model
        self.summ = summ  #Summarising Model
        self.memory = memory #Memory Of the Chat
        self.summarising = summarising #Summarising Status
        self.response = ""
        self.tools = [self.coding_tool,]
        self.codingmemory = [{
            "role" : "system",
            "content": self.coding_agent_prompt
        }]
        
        
    def summarise(self,memory_snapshot):
        
        
        memory_content = ""

        for i in memory_snapshot:

            if isinstance(i,dict):
                memory_content += i.get("content","")

            else:
                memory_content += i.content or ""

        messages_format = [{
            "role": "user",
            "content": f"{self.the_real_content}\n\n{memory_content}"
        }]

        summarised_memory = chat(
            model=self.summ,
            messages = messages_format,
            think=False
        )
        
        return summarised_memory.message.content
              
        
    def show_memory(self):
        """Used to show/display the stored memory"""
        return self.memory[0]["content"]


    def background_summarise(self,memory_snapshot):
        
        print("\n\n[Background] Summarising memory...\n")

        try:

            summary = self.summarise(memory_snapshot)

            if self.memory[:len(memory_snapshot)] == memory_snapshot:

                self.memory[:len(memory_snapshot)] = [{
                    "role":"system",
                    "content":f"Memory of the whole chat is {summary} "
                }]

        except Exception as e:
            print("\n[Background] Error:", e)

        finally:
            self.summarising = False


    def chat(self):
        counter = 0
        while True:
            if counter >= 5 and not self.summarising:

                self.summarising = True

                memory_snapshot = self.memory.copy()

                thread = threading.Thread(
                    target=self.background_summarise,
                    args=(memory_snapshot,)
                )

                thread.start()
            prompt = input("Enter The Prompt: ")

            self.memory.append({
                "role": "user",
                "content": prompt
            })

            result = chat(
                model=self.chatm,
                messages=self.memory,
                tools=self.tools,
                think=False
            )
            print("CONTENT:", repr(result.message.content))
            print("TOOL CALLS:", result.message.tool_calls)
            print("THINKING:", repr(result.message.thinking))

            if result.message.tool_calls:

                self.memory.append(result.message)

                for tool_call in result.message.tool_calls:

                    if tool_call.function.name == "coding_tool":

                        tool_prompt = tool_call.function.arguments["prompt"]


                        print(f"\n[Tool] coding_tool: {tool_prompt}")
                        
                        
                        
                        tool_result = self.coding_tool(
                            prompt=tool_prompt
                        )


                        print(f"[Tool Result] {tool_result}\n")

                        self.memory.append({
                            "role": "tool",
                            "content": tool_result,
                            "tool_name": tool_call.function.name
                        })


                result = chat(
                    model=self.chatm,
                    messages=self.memory,
                    tools=self.tools,
                    think=False
                )
            response = result.message.content or ""
            self.memory.append({
                "role": "assistant",
                "content": response})

            print(response)
            counter += 1


    def coding_tool(self, prompt: str):
        """Generate and execute Python code for tasks that require creating,
    modifying, deleting, reading, or interacting with local files,
    folders, programs, or the operating system.
    Use this tool when the user asks to perform an actual computer-side
    action rather than merely explain how to do it."""
        
        result = chat(
            model="qwen2.5-coder:3b",
            messages=[
                {
                    "role": "system",
                    "content": self.coding_agent_prompt},
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            think=False
        )
        code = result.message.content

        try:
            code = code.strip()

            if code.startswith("```python"):
                code = code[len("```python"):].strip()

            if code.endswith("```"):
                code = code[:-3].strip()
            
            compile(code, "<generated_code>", "exec")
            exec(code)
            return "Task performed anad cOde executed successfully."

        except Exception as e:
            return f"Error executing program: {e}\n\nGenerated code:\n{code}"
