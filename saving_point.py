#Organized but has global variables that might interfere

import os
import json

class SavePoint:
    def __init__(self, checkpoint_path='save_file1.json', data_path='save_data_file3.json'):
        self.checkpoint_path = checkpoint_path
        self.data_path = data_path

    def save_checkpoint(self, data_list):
        # Load existing data (if necessary)
        checkpoint = self.load_checkpoint() or []

        # Append new data
        checkpoint.extend(data_list)

        # Save updated data
        with open(self.checkpoint_path, 'w', encoding='utf-8') as f:
            json.dump(checkpoint, f)

    def load_checkpoint(self):
        if os.path.exists(self.checkpoint_path):
            with open(self.checkpoint_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def save_data(self, key, value):
        # Load existing data
        data = self.load_data() or {}

        # Update with new key-value pair
        data[key] = value

        # Save updated data
        with open(self.data_path, 'w', encoding='utf-8') as f:
            json.dump(data, f)

    def load_data(self):
        if os.path.exists(self.data_path):
            with open(self.data_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None