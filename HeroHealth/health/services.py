from ai_engine.services import analyze_symptoms_ai
from ai_engine.safety import is_safe_query, clean_query_text
from .models import Consultation

def process_consultation(user, symptoms_text, image_path=None):
    # Validate query
    is_safe, error_msg = is_safe_query(symptoms_text)
    if not is_safe:
        return None, error_msg

    # Clean text
    clean_text = clean_query_text(symptoms_text)

    # Call AI Engine
    ai_response = analyze_symptoms_ai(clean_text, image_path)

    # Save to database
    consultation = Consultation.objects.create(
        user=user if user.is_authenticated else None,
        symptoms=symptoms_text,
        result_json=ai_response
    )
    
    return consultation, None
