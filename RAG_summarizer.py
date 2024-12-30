#Summarizes rag responses to one sentence
#untest

import os
import getpass
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
import prompts
from dotenv import load_dotenv

# Securely get and set the API key
#os.environ['ANTHROPIC_API_KEY'] = getpass.getpass("Enter your Anthropic API key: ")
# Initialize the model with the API key from the environment
#model = ChatAnthropic(model="claude-3-sonnet-20240229", max_tokens_to_sample=4096)
class RagSummary:
    def __init__(self):
        load_dotenv()
        os.environ['OPENAI_API_KEY'] = os.getenv("AI_KEY")
        self.model = ChatOpenAI(model="gpt-4o-mini", max_tokens=4096)

    def main(self):
        with open('RAG_response.txt', 'r', encoding='utf-8') as file:
            RAG_resp = file.read()

        x = self.summarizing_outline(RAG_resp)
        y = self.add_more_details(RAG_resp, x)
        print(y)

    def summarizing_outline(self, RAG_resp):
        system_message = prompts.system_message_PI
        human_prompt_4 = prompts.human_prompt_4(RAG_resp)
        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=human_prompt_4),
        ]

        # Invoke the model and parse the result
        result = self.model.invoke(messages)
        parsed_result = StrOutputParser().invoke(result)

        # Save the result to a file
        with open('RAG_summed_1.txt', 'w', encoding='utf-8') as file:
            file.write(str(parsed_result))

        return parsed_result

    def add_more_details(self, RAG_resp, summed_sentence):
        system_message = prompts.system_message_PI
        human_prompt_5 = prompts.human_prompt_5(RAG_resp, summed_sentence)
        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=human_prompt_5),
        ]

        # Invoke the model and parse the result
        result = self.model.invoke(messages)
        parsed_result = StrOutputParser().invoke(result)

        # Save the result to a file
        print("Summarized")
        with open('RAG_summed_2.txt', 'w', encoding='utf-8') as file:
            file.write(str(parsed_result))
        
        return parsed_result

if __name__ == "__main__":
    processor = RagSummary()
    processor.main()