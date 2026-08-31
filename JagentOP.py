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
    def __init__(self,chatm:str,summ:str,memory:list,summarising=False):
        self.chatm = chatm #ChaT model
        self.summ = summ  #Summarising Model
        self.memory = memory #Memory Of the Chat
        self.summarising = summarising #Summarising Status
        self.response = ""
        
    def summarise(self):
        
        
        memory_content = "".join(i["content"] for i in self.memory)

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
            summary = self.summarise()
            self.memory.clear()
            self.memory.append({
                "role":"system",
                "content":f"Memory of the whole chat is {summary} "
            })
        except Exception as e:
            print("\n[Background] Error:", e)
        finally:
            self.summarising = False

    def chat(self):
        counter = 5
        while True:
            if counter > 5 and self.summarising == True:
                memory_snapshot = self.memory.copy()
                thread = threading.Thread(target=self.background_summarise,args=(memory_snapshot,))
                thread.start()
                
                
            prompt = str(input("Enter The Prompt: "))
            self.memory.append({
                "role":"user",
                "content": prompt
            }) 
            result = chat(
                model=self.chatm,
                messages = self.memory
            )
            
            self.memory.append({
                "role":"assistant",
                "content" : f"{result.message.content}"
            })
            
            print(result.message.content)
            counter +=1


