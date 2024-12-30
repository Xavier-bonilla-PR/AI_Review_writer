import re
import os
import time
from openai import OpenAI
from dotenv import load_dotenv, find_dotenv
import prompts

class OutlineProcessor:
    def __init__(self, openai_api_key, model="gpt-4o-mini", temperature=0.2, max_tokens=3000):
        load_dotenv(find_dotenv())
        self.client = OpenAI(api_key=openai_api_key)
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    @staticmethod
    def save_list_to_text(my_list, filename):
        with open(filename, 'w', encoding='utf-8') as file:
            for item in my_list:
                file.write(str(item) + '\n')

    @staticmethod
    def separate_by_roman_numerals(text):
        roman_numerals = [
            'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X',
            'XI', 'XII', 'XIII', 'XIV', 'XV', 'XVI', 'XVII', 'XVIII', 'XIX', 'XX'
        ]
        pattern = r'(\b(?:' + '|'.join(roman_numerals) + r')\.)'
        parts = re.split(pattern, text)
        result = []
        i = 1
        while i < len(parts):
            if parts[i-1].strip()[:-1] in roman_numerals:
                result.append(parts[i-1] + parts[i])
                i += 2
            else:
                i += 1
        return result

    def get_summary(self, messages):
        completion = self.client.chat.completions.create(
            model=self.model, 
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return completion.choices[0].message.content

    def process_outline(self, outline_file, book_file, output_file):
        with open(outline_file, "r", encoding="utf-8") as file:
            text = file.read()

        outline = self.separate_by_roman_numerals(text)

        with open(book_file, "r", encoding="utf-8") as file:
            book = file.read()

        litreviewlist = []
        for item in outline:        
            print(item)
            system_message = prompts.system_message_4
            prompt = prompts.generate_prompt_4a(book, item)

            messages = [
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ]
            response = self.get_summary(messages)
            print(response)
            litreviewlist.append(response)
            time.sleep(1)

        self.save_list_to_text(litreviewlist, output_file)

def main():
    api_key = os.getenv('AI_KEY')
    processor = OutlineProcessor(api_key=api_key)
    processor.process_outline('outline_combined6.txt', 'data_summary_full.txt', 'outline_infd_2.txt')

if __name__ == "__main__":
    main()