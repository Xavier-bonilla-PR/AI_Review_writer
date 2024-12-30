#Puts outline into a list that can be easily read
#organized


import re

class OutlineSplit:
    def __init__(self):
        self.roman_numerals = ['I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 
                               'XI', 'XII', 'XIII', 'XIV', 'XV', 'XVI', 'XVII', 'XVIII', 'XIX', 'XX']

        # Create regex patterns
        self.roman_pattern = (
            r'(' + '|'.join(re.escape(num + '.') for num in self.roman_numerals) + r')\s*([^\n]+)(?:\n|$)'
            r'((?:(?!' + '|'.join(re.escape(num + '.') for num in self.roman_numerals) + r').)*)'
        )
        self.letter_pattern = r'([A-Z]\. )'
        self.arabic_pattern = r'(\d+\. )'

    def process_text_file(self, file_path):
        try:
            # Read the text file
            text = self.read_text_file(file_path)
            
            # Process the text
            result = self.separate_outline(text)
            
            return result
        
        except FileNotFoundError:
            print(f"Error: The file {file_path} was not found.")
        except Exception as e:
            print(f"An error occurred: {str(e)}")

    def separate_outline(self, text):
        # Split the text by Roman numerals
        roman_parts = re.findall(self.roman_pattern, text, re.DOTALL)
        result = []

        for roman_title, roman_subtitle, roman_content in roman_parts:
            roman_section = [roman_title, [], roman_subtitle.strip()]

            # Split the content by letters
            letter_parts = re.split(self.letter_pattern, roman_content)

            if len(letter_parts) > 1:
                for i in range(1, len(letter_parts), 2):
                    letter_title = letter_parts[i]
                    letter_content = letter_parts[i + 1].strip() if i + 1 < len(letter_parts) else ""

                    # Extract subtitle (everything before the first newline)
                    subtitle_match = re.match(r'([^\n]+)(?:\n|$)', letter_content)
                    subtitle = subtitle_match.group(1).strip() if subtitle_match else ""

                    # Split remaining content by Arabic numerals
                    remaining_content = letter_content[len(subtitle):].strip()
                    arabic_parts = re.split(self.arabic_pattern, remaining_content)
                    arabic_section = []

                    if len(arabic_parts) > 1:
                        for j in range(1, len(arabic_parts), 2):
                            arabic_title = arabic_parts[j]
                            arabic_content = arabic_parts[j + 1].strip() if j + 1 < len(arabic_parts) else ""
                            arabic_section.append([arabic_title, arabic_content])
                    else:
                        # If there are no Arabic numerals, add all remaining content as a single item
                        arabic_section.append(["", remaining_content])

                    letter_section = [letter_title, arabic_section, subtitle]
                    roman_section[1].append(letter_section)
            else:
                # If there are no letters, add all content under the Roman numeral
                subtitle_match = re.match(r'([^\n]+)(?:\n|$)', roman_content)
                roman_subtitle = subtitle_match.group(1).strip() if subtitle_match else ""
                roman_section[1].append(["", [["", roman_content]], roman_subtitle])

            result.append(roman_section)

        return result
    
    @staticmethod
    def read_text_file(file_path):
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()

 

def main():
    text = """
    I. First main point
    A. Subpoint A
        - Detail 1
        1. Detail 2
    B. Subpoint B
        1. Detail 1
        2. Detail 2
    II. Second main point
        A. Subpoint A
        B. Subpoint B
    """

    """
    [['I.', 
    [['A. ', [['1. ', 'Detail 1'], ['2. ', 'Detail 2']], 'Subpoint A'], 
    ['B. ', [['1. ', 'Detail 1'], ['2. ', 'Detail 2']], 'Subpoint B']], 'First main point'], 
    ['II.', 
    [['A. ', [['', '']], 'Subpoint A'], 
    ['B. ', [['', '']], 'Subpoint B']], 'Second main point']]
    """
    z = OutlineSplit()
    file_path= 'outline_improved_1.txt'
    outline_list = z.process_text_file(file_path)
    # print(len(separated_2_list))
    # print(len(separated_2_list[0]))
    # print(len(separated_2_list[0][1]))
    # print(len(separated_2_list[0][1][0]))
    #print(separated_2_list[0][1][0][3])
    print("Amount of roman numeral:")
    print(f"Outline_list size: {len(outline_list)}")
    for i in range(len(outline_list)):
        print("Amount of letter:")
        print(f"outline_list[{i}] size: {len(outline_list[i])}")
        for j in range(len(outline_list[i])):
            print("Roman numeral title:")
            print(f"outline_list[{j}][2]: {outline_list[j][2]}")
  


if __name__ == "__main__":
    main()
