#Labels doc whether literature review or Primary
#Very prettily organized 
import os
from openai import OpenAI
from dotenv import load_dotenv
import PyPDF2
import prompts 
import re
import time
import warnings
from PyPDF2.errors import PdfReadWarning
import json

warnings.filterwarnings("ignore", category=PdfReadWarning)

class ArticleLabel:
    def __init__(self, folder_path, model="gpt-4o-mini", temperature=0.3, max_tokens=3000):
        load_dotenv()
        self.folder_path = folder_path
        self.client = OpenAI(api_key=os.getenv('AI_KEY'))
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def name_getter(self):
        file_names = os.listdir(self.folder_path)
        return file_names

    def pdf_cleaner(self, doc):
        book = ""
        file_path = os.path.join(self.folder_path, doc)
        with open(file_path, "rb") as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                book += page.extract_text() + " "
        return book

    def get_summary(self, messages):
        completion = self.client.chat.completions.create(
            model=self.model, 
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return completion.choices[0].message.content

    def parse_output(self, text, doc):
        classification = re.search(r"Final Classification: (.+)", text)
        confidence = re.search(r"Confidence Level: (.+)", text)

        classification = classification.group(1) if classification else "Unknown"
        confidence = confidence.group(1) if confidence else "Unknown"

        return [doc, classification.strip(), confidence]

    def review_pdfs(self):
        labels = []
        doc_names = self.name_getter()
        print(f"Found {len(doc_names)} documents")
        
        for doc in doc_names:
            print(f"Processing: {doc}")
            book_all = self.pdf_cleaner(doc)
            #Added this
            book = book_all[1:3000]
            messages = [
                {"role": "system", "content": prompts.system_message_2},
                {"role": "user", "content": prompts.generate_prompt_2a(book)} #changed this
            ]
            response = self.get_summary(messages)
            print(response)
            # label = self.parse_output(response, doc)
            labels.append((doc, response)) #label
            time.sleep(0.75)
        
        return labels

def main():
    #Labels and saves in data_labels_1.txt
    reviewer = ArticleLabel('H2S_review')
    results = reviewer.review_pdfs()
    print(results)
    with open('data_labels_1.txt', 'w') as file:
        json.dump(results, file, indent=4)

    

if __name__ == "__main__":
    main()
