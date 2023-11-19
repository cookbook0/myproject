import re

#Extracts a float value from a text string.. UPDATE TO HANDLE COMMAS
def extract_float_from_text(text):
    if text:
        match = re.search(r'\d+\.\d+', text)
        if match:
            return float(match.group())
    return None

  #Calculates the percentage difference between two values
def calculate_percentage_difference(old_value, new_value):
    if old_value is not None and new_value is not None and old_value != 0:
        return round(((old_value - new_value) / old_value) * 100, 2)
    return None