#Reads pdf and turns to txt file
#Removes reference section
#Organized but could be better

#Modified to eliminate the only litrevs
#untested
import os
from PyPDF2 import PdfReader
import re
import json


#Gets a list of all the document names in the folder
def list_files(file_path):
 
    # Get the list of files in the specified folder
    files = os.listdir(file_path)
    files.sort()

    return files

class RefRemove:
    def __init__(self, pdf_path, output_path):
        self.pdf_path = pdf_path
        self.output_path = output_path
        self.reference_headers = [
            r'\bReferences\b',
            r'\bREFERENCES\b',
            r'\bWorks Cited\b',
            r'\bBibliography\b',
            r'\bLiterature Cited\b'
        ]

    
    #Uses regex to match reference section
    def identify_references_section(self, text):
        """
        Identify the start of the references section 
        """
        # Combine all patterns into a single regex
        pattern = '|'.join(self.reference_headers)
        
        # Find all matches
        matches = list(re.finditer(pattern, text))
        
        if matches:
            # If they match the regex then only output half without ref
            last_match = matches[-1]
            start_index = last_match.start()
            print(f"Matched '{last_match.group()}' at index {start_index}")
            print(f"Length of text before references: {len(text[:start_index])}")
            return text[:start_index]  
        else:
            print("References section not found")
            print(text[:500])
            return text

    def pdf_to_txt(self):
        """
        Convert PDF to text, tag the references section.
        """
        try:
            # Open the PDF file
            with open(self.pdf_path, 'rb') as file:
                pdf_reader = PdfReader(file)
                
                # Extract text from each page
                text_content = []
                for page in pdf_reader.pages:
                    text_content.append(page.extract_text())
                
                # Join all pages
                full_text = "\n".join(text_content)
                
                # Identify and tag the references section
                tagged_text = self.identify_references_section(full_text)
                
                
                # Write to output file
                with open(self.output_path, 'w', encoding='utf-8') as output_file:
                    output_file.write(tagged_text)
                
                print(f"Successfully converted {self.pdf_path} to {self.output_path}")
        
        except Exception as e:
            print(f"An error occurred: {str(e)}")

def main():
    # Configure your input and output files here
    #pdf_path = "H2S_review_unk_dimension/ref14_no1rstpg.pdf"
    #output_path = "data/ref14_noref.txt"

    reflitname = list_files('H2S_review')
    i = 0
    for item in reflitname:
        pdf_path = f'H2S_review/{item}'
        output_path = f'data/{item[:-4]}_noref.txt'
        converter = RefRemove(pdf_path, output_path)
        converter.pdf_to_txt()

if __name__ == "__main__":
    main()