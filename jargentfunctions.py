import json
def exit(memory:list):
    with open("memory.json", "w") as f:
        
        json.dump(memory,f,indent=4)
        print("Memory Folder Creared sucessfully")

def load_memory():
    with open("memory.json", "r") as f:
        memory = json.load(f)
        return memory
        
    