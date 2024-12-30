#Summarizes articles for Intro, hypothesis, experiment, results, analysis, conclusion, overall
#Neetly organized but should move some prompts to prompts.py

import json
import os
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
import PyPDF2
import prompts 
import re
import warnings
from PyPDF2.errors import PdfReadWarning
import time

warnings.filterwarnings("ignore", category=PdfReadWarning)

class ArticleSummary:
    #initializes variables and list and dicts
    def __init__(self, input_file, output_file, folder_name):
        self.folder_name = folder_name
        self.input_file = input_file
        self.output_file = output_file
        self.data_list = []
        self.data_ref = []
        self.nested_dict = {}
        
        #initializes the llm 
        load_dotenv()
        self.client = OpenAI(api_key=os.getenv('AI_KEY'))
        self.model = "gpt-4o-mini"
        self.temperature = 0.3
        self.max_tokens = 1600

    #open txt and converts string to a list using json and saves in data_list
    def load_data(self):
        with open(self.input_file, "r", encoding="utf-8") as file:
            document_content = file.read()
        self.data_list = json.loads(document_content)

    #extracts document name if its a primary article and saves in data_ref
    def process_data(self):
        for item in self.data_list:
            if item[1] == 'Final Classification: Primary Research Article':
                self.data_ref.append(item[0])

    #Collects the body text of the article and saves in variable
    def pdf_cleaner(self, doc):
        book = ""
        file_path = f'{self.folder_name}/{doc}'
        with open(file_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            total_pages = len(reader.pages)
            for page_number in range(total_pages):
                page = reader.pages[page_number]
                book += page.extract_text() + " "
        return book

    #To actually run the llm, conditional on messages since the document it reads changes on each run
    def get_summary(self, messages):
        completion = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return completion.choices[0].message.content

    #Identifies section as **intro** and separates them into a list
    def parse_research_analysis(self, text):
        sections = re.split(r'\n(?=\d+\.\s+\*\*)', text)
        parsed_data = {}
        
        for section in sections:
            match = re.match(r'(\d+\.\s+\*\*[^*]+\*\*)\n(.*)', section, re.DOTALL)
            if match:
                title = match.group(1).strip()
                content = match.group(2).strip()
                content = re.sub(r'\*\*|\{[^}]*\}', '', content)
                paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
                parsed_data[title] = paragraphs[0] if len(paragraphs) == 1 else paragraphs
        
        return parsed_data

    #Takes the body text and runs llm
    def analyze_single_document(self, doc):
        print(f"Analyzing: {doc}")
        book = self.pdf_cleaner(doc)
        system_message = prompts.system_message_1
        prompt = prompts.generate_prompt_1(book)
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ]
        response = self.get_summary(messages)
        return self.parse_research_analysis(response)

    #saves the llm response in a dictionary
    def analyze_research(self):
        self.load_data()
        self.process_data()

        for item in self.data_ref:
            self.nested_dict[item] = self.analyze_single_document(item)
            time.sleep(1.5)

    #saves the dictionary in a file
    def save_results(self):
        with open(self.output_file, 'w') as file:
            json.dump(self.nested_dict, file, indent=4)

    #Activates the feedback function
    def run(self):
        self.analyze_research()
        self.save_results()
        self.feedback_loop()

    #passes response through an llm to check for error. 
    def feedback_loop(self):
        
        print("\nCurrent documents analyzed:")
        for i, doc in enumerate(self.nested_dict.keys(), 1):
            print(f"{i}. {doc}")

        # Here goes the llm bot
        messages = [
            {"role": "system", "content": 'You are a helpful assistant.'},
            {"role": "user", "content": 'Analyze the document and identify if there is any ref missing its analysis. A ref that is missing its analysis should look like this: "[document name].pdf: {1. **Hypothesis Identification**: [], 2. **Experimental Design Analysis**: [], 3. **Results Interpretation**: [], 4. **Discussion and Conclusions Evaluation**: [], 5. **Final Judgment**: []}" or "[document name].pdf: {}" If there is any ref missing its analysis, then respond with the name of the document like this [document_name.pdf]. If everything looks good then respond [None]'}
        ]
        choice = self.get_summary(messages)

        print(f"Reanalysis: {choice}")

        if choice.lower() == '[none]':
            print("No reanalysis needed.")
        else:
            try:
                index = int(choice.strip('[]')) - 1
                doc = list(self.nested_dict.keys())[index]
                
                print(f"\nReanalyzing document: {doc}")
                new_analysis = self.analyze_single_document(doc)
                
                print("\nNew analysis results:")
                for key, value in new_analysis.items():
                    print(f"{key}: {value}")
                
                self.nested_dict[doc] = new_analysis
                print("Results updated.")
                self.save_results()
            except (ValueError, IndexError):
                print(f"Invalid input: {choice}")

    def topic_finder(self):
        book = str(self.nested_dict)
        system_message = prompts.system_message_1
        prompt = prompts.generate_prompt_1a(book)
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": prompt}
        ]
        response = self.get_summary(messages)
        return response

if __name__ == "__main__":
    analyzer = ArticleSummary("data_labels.txt", "data_summary_full_.txt")
    analyzer.run()