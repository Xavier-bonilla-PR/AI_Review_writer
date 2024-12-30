#Makes and combines outlines
#Change file names
import ast
import random
import os
import getpass
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import StrOutputParser
import prompts

class OutlineMaker:
    def __init__(self, file_name_in, file_name_communication, file_name_result):
        self.file_name_in = file_name_in
        self.file_name_communication = file_name_communication
        self.file_name_result = file_name_result
        self.model = None
        self.dict_data = None
        self.result_dict = None

    def setup_api_key(self):
        os.environ['ANTHROPIC_API_KEY'] = getpass.getpass("Enter your Anthropic API key: ")
        self.model = ChatAnthropic(model="claude-3-sonnet-20240229", max_tokens_to_sample=4096)

    @staticmethod
    def txt_to_dict(file_path):
        with open(file_path, 'r') as file:
            dict_str = file.read()
        dict_data = ast.literal_eval(dict_str)
        print(type(dict_data))
        return dict_data

    @staticmethod
    def split_dict(original_dict, chunk_size=10, min_last_size=5):
        items = list(original_dict.items())
        result = []
        
        while items:
            if len(items) >= chunk_size:
                chunk = random.sample(items, chunk_size)
                for item in chunk:
                    items.remove(item)
                result.append(dict(chunk))
            else:
                chunk = items
                items = []
                if result and len(chunk) < min_last_size:
                    result[-1].update(dict(chunk))
                else:
                    result.append(dict(chunk))
        
        return result

    def load_data(self, chunk_size=10):
        self.dict_data = self.txt_to_dict(self.file_name_in)
        self.result_dict = self.split_dict(self.dict_data, chunk_size)
        print(f"Number of chunks: {len(self.result_dict)}")

    def focused_outlines(self, topic):
        outline_list = []
        for item in self.result_dict:
            system_message = prompts.system_message_PI
            human_prompt = prompts.human_prompt(item, topic)
            messages = [
                SystemMessage(content=system_message),
                HumanMessage(content=human_prompt),
            ]

            result = self.model.invoke(messages)
            parsed_result = StrOutputParser().invoke(result)

            outline_list.append(parsed_result)
            print(parsed_result)

        with open(self.file_name_communication, 'w', encoding='utf-8') as file:
            file.write(str(outline_list))

    def combining_outline(self, topic):
        with open(self.file_name_communication, 'r') as file:
            outlines = file.read()

        system_message = prompts.system_message_PI
        human_prompt_3 = prompts.human_prompt_3(outlines, topic)
        messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=human_prompt_3),
        ]

        result = self.model.invoke(messages)
        parsed_result = StrOutputParser().invoke(result)

        print(parsed_result)

        with open(self.file_name_result, 'w', encoding='utf-8') as file:
            file.write(str(parsed_result))

def main():
    outline_maker = OutlineMaker("data_summary_full_1.txt", "data_comm_1.txt", "combined_outline_1.txt")
    outline_maker.setup_api_key()
    

    outline_maker.load_data()
    
    topic = 'hydrogen sulfide donating molecules for treating diseases'
    outline_maker.focused_outlines(topic)
    outline_maker.combining_outline(topic)

if __name__ == "__main__":
    main()