#Finds all the " - " sections in an outline and puts them in a list
#Replaces the " - " with new ones from a json file
#organized

import re
import json

class SectionSplit:
    def __init__(self, json_file_path):
        self.json_file_path = json_file_path

    def parse_outline(self, text):
        pattern = r'^\s*-\s*(.+)$'
        matches = re.finditer(pattern, text, re.MULTILINE)
        return [match.group(1).strip() for match in matches]

    def replace_bullet_points(self, text):
        # Load the dictionary from the JSON file
        try:
            with open(self.json_file_path, 'r') as f:
                replacements = json.load(f)
        except FileNotFoundError:
            print(f"Error: The file {self.json_file_path} was not found.")
            return text
        except json.JSONDecodeError:
            print(f"Error: The file {self.json_file_path} is not a valid JSON file.")
            return text

        lines = text.split('\n')
        new_lines = []

        for line in lines:
            if line.strip().startswith('-'):
                # Remove leading/trailing whitespace and the bullet point
                key = line.strip()[1:].strip()
                
                # Check if the key exists in the dictionary
                if key in replacements:
                    new_lines.append(f"    - {replacements[key]}")
                else:
                    new_lines.append(line)  # Keep original if key not found
            else:
                new_lines.append(line)

        return '\n'.join(new_lines)
