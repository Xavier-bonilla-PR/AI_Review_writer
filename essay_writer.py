import ast
import random
import os
import getpass
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
import prompts
import re
import json
from dotenv import load_dotenv
load_dotenv()

os.environ['OPENAI_API_KEY'] = os.getenv("AI_KEY")

# Initialize the model with the API key from the environment
model = ChatOpenAI(model="o1-mini-2024-09-12", max_tokens=4096)

# # Securely get and set the API key
# os.environ['ANTHROPIC_API_KEY'] = getpass.getpass("Enter your Anthropic API key: ")

# # Initialize the model with the API key from the environment
# model = ChatAnthropic(model="claude-3-sonnet-20240229", max_tokens_to_sample=4096)



class EssayWriter:
    def __init__(self, model):
        self.model = model

    def write_section(self, section):
        system_message = prompts.system_message_PI
        human_prompt = prompts.human_prompt_2(section)
        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=human_prompt),
        ]

        # Invoke the model and parse the result
        result = self.model.invoke(messages)
        parsed_result = StrOutputParser().invoke(result)

        return parsed_result

    def writing_abstract(self, lit_rev, topic):

        system_message = prompts.system_message_PI
        human_prompt = prompts.human_prompt_6(lit_rev, topic)
        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=human_prompt),
        ]

        # Invoke the model and parse the result
        result = model.invoke(messages)
        parsed_result = StrOutputParser().invoke(result)

        # Print the result

        return(parsed_result)
    
    def writing_title(self, abstract):

        system_message = prompts.system_message_PI
        human_prompt = prompts.human_prompt_7(abstract)
        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=human_prompt),
        ]

        # Invoke the model and parse the result
        result = model.invoke(messages)
        parsed_result = StrOutputParser().invoke(result)

        # Print the result

        return(parsed_result)
    
    @staticmethod
    def add_entry_to_file(filename, new_entry):
        with open(filename, 'a', encoding='utf-8') as file:
            file.write(new_entry + '\n')

    # Save to JSON file
    @staticmethod
    def add_entry_to_json(file_name, dictionary):
        with open(file_name, "w") as file:
            json.dump(dictionary, file)

    

def main():
    file_path = 'lit_rev_3.txt'
    with open(file_path, 'r', encoding='utf-8') as file:
        lit_rev = file.read()
    z = EssayWriter(model)
    outline_list =[] #fix
    title = 'Abstract'
    z.add_entry_to_file('lit_full_rev_3.txt', title)
    abstract = z.writing_abstract(lit_rev)
    z.add_entry_to_file('lit_full_rev_3.txt', abstract)
    for i in range(len(outline_list)): #Roman numberal -7
        
        roman_title = outline_list[i][2]
        z.add_entry_to_file('lit_rev_3.txt', roman_title)

        for j in range(len(outline_list[i][1])):
            subtitle = outline_list[i][1][j][2]
            item = str(outline_list[i][1][j][1])
            x = z.write_section(item)
            
            z.add_entry_to_file('lit_rev_3.txt', subtitle)
            z.add_entry_to_file('lit_rev_3.txt', x)

if __name__ == "__main__":
    main()

