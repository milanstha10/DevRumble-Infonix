import re

def is_safe_query(symptoms_text):
    if not symptoms_text or len(symptoms_text.strip()) < 5:
        return False, "Symptom description is too short. Please provide a more detailed description of how you are feeling."
    
    # Check for basic gibberish or spam (e.g. repeated single characters, random strings)
    if re.match(r'^(.)\1{4,}$', symptoms_text.strip()):
        return False, "Input looks like gibberish. Please write down actual symptoms."

    return True, ""

def clean_query_text(symptoms_text):
    # Remove script tags or HTML tags if any to prevent XSS
    clean = re.sub(r'<[^>]*>', '', symptoms_text)
    return clean.strip()
