import json
import logging
from django.conf import settings
from .prompts import SYSTEM_PROMPT

logger = logging.getLogger(__name__)

# Try to import google-genai. If not available, we handle it gracefully.
try:
    from google import genai
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False

def run_local_triage(symptoms_text):
    """
    Comprehensive rule-based offline symptom analyzer to serve as a high-fidelity fallback.
    """
    text = symptoms_text.lower()
    
    # Default values
    disclaimer = (
        "OFFLINE MODE: This is a rule-based triage assessment based on matching keywords. "
        "It is NOT a medical diagnosis. Please consult a qualified doctor or visit a hospital."
    )
    severity = "Low"
    probable_causes = []
    recommended_actions = [
        "Monitor your symptoms closely.",
        "Ensure you are resting and staying hydrated.",
        "Consult a general physician if symptoms persist for more than 48 hours."
    ]
    suggested_specialty = "General Medicine"
    urgency_alert = "Your symptoms appear to be mild. Monitor closely and rest."

    # Emergency check (Chest pain, severe breathing, stroke signs)
    if any(k in text for k in ["chest pain", "heart attack", "difficulty breathing", "shortness of breath", "cannot breathe", "stroke", "paralysis", "unconscious", "heavy bleeding"]):
        severity = "Urgent"
        suggested_specialty = "Cardiology / Emergency Medicine"
        probable_causes = [
            {
                "cause": "Acute Cardiac Event or Respiratory Distress",
                "likelihood": "High",
                "description": "Symptoms such as chest pain or breathing difficulty can indicate a serious heart or lung issue."
            }
        ]
        recommended_actions = [
            "CALL FOR AN AMBULANCE immediately (Call 102 in Nepal).",
            "Sit in a comfortable position and loosen any tight clothing.",
            "Do NOT perform physical exertion. Do NOT drive yourself to the hospital.",
            "If you have prescribed emergency medicine (like nitroglycerin or an inhaler), use it now."
        ]
        urgency_alert = "CRITICAL: Please seek emergency medical care immediately!"
        
    # Fever / Flu
    elif any(k in text for k in ["fever", "high temp", "chills", "sweating", "cough", "cold", "flu", "sore throat", "runny nose"]):
        severity = "Medium"
        suggested_specialty = "General Medicine"
        probable_causes = [
            {
                "cause": "Viral Infection (Influenza / Common Cold)",
                "likelihood": "High",
                "description": "A very common cause of fever, cough, and body aches."
            },
            {
                "cause": "Respiratory Tract Infection",
                "likelihood": "Medium",
                "description": "Bacterial or viral infection affecting the throat, airways, or lungs."
            }
        ]
        recommended_actions = [
            "Get plenty of bed rest and drink warm fluids (water, herbal teas).",
            "Monitor body temperature. You may take Paracetamol (if not allergic) to manage fever.",
            "If fever exceeds 103°F (39.4°C) or lasts more than 3 days, consult a physician."
        ]
        urgency_alert = "Moderate: Monitor your temperature and seek care if it persists."

    # Abdominal / Gastrointestinal
    elif any(k in text for k in ["stomach pain", "abdominal", "vomit", "diarrhea", "nausea", "food poisoning", "loose motion", "cramp"]):
        severity = "Medium"
        suggested_specialty = "Gastroenterology"
        probable_causes = [
            {
                "cause": "Gastroenteritis / Food Poisoning",
                "likelihood": "High",
                "description": "Inflammation of the stomach and intestines, typically due to contaminated food or water."
            },
            {
                "cause": "Acid Reflux / Dyspepsia",
                "likelihood": "Medium",
                "description": "Stomach acid flowing back into the food pipe, causing pain or discomfort."
            }
        ]
        recommended_actions = [
            "Stay hydrated by drinking Oral Rehydration Salts (ORS / Jeevan Jal) in clean water.",
            "Eat light, bland foods (like rice, banana, curd) and avoid oily/spicy foods.",
            "If vomiting prevents fluid intake, or if you see blood in vomit or stool, seek immediate care."
        ]
        urgency_alert = "Moderate: Keep hydrated. If dehydration signs occur, visit a clinic."

    # Skin / Dermatological
    elif any(k in text for k in ["rash", "itch", "skin", "redness", "hives", "allergy", "insect bite", "boil"]):
        severity = "Low"
        suggested_specialty = "Dermatology"
        probable_causes = [
            {
                "cause": "Allergic Dermatitis / Hives",
                "likelihood": "High",
                "description": "A skin reaction to an allergen, chemical, or insect bite."
            },
            {
                "cause": "Fungal or Bacterial Skin Infection",
                "likelihood": "Medium",
                "description": "Common skin conditions in humid environments."
            }
        ]
        recommended_actions = [
            "Avoid scratching the affected area to prevent secondary bacterial infection.",
            "Apply a cool, damp compress to soothe the itching.",
            "Consult a dermatologist if the rash spreads quickly or is accompanied by fever."
        ]
        urgency_alert = "Low: Manageable at home. Seek specialist care if it worsens."

    # Bone / Joint / Injury
    elif any(k in text for k in ["fracture", "broken bone", "joint pain", "sprain", "strain", "swelling", "fall", "injury", "back pain"]):
        severity = "Medium"
        suggested_specialty = "Orthopedics"
        probable_causes = [
            {
                "cause": "Ligament Sprain or Muscle Strain",
                "likelihood": "High",
                "description": "Stretching or tearing of ligaments/muscles, common after slips or falls."
            },
            {
                "cause": "Bone Fracture",
                "likelihood": "Medium",
                "description": "A partial or complete break in a bone, typically accompanied by severe pain and swelling."
            }
        ]
        recommended_actions = [
            "Follow the R.I.C.E. protocol: Rest, Ice, Compression, Elevation.",
            "Immobilize the injured limb using a splint or bandage if possible.",
            "Get an X-ray to rule out or diagnose a bone fracture."
        ]
        urgency_alert = "Moderate: Avoid putting weight on the limb and consult a doctor."

    return {
        "disclaimer": disclaimer,
        "severity": severity,
        "probable_causes": probable_causes,
        "recommended_actions": recommended_actions,
        "suggested_specialty": suggested_specialty,
        "urgency_alert": urgency_alert
    }

def analyze_symptoms_ai(symptoms_text, image_path=None):
    """
    Main triage coordinator. Attempts to query Google Gemini.
    Falls back to offline rule engine if API key is not present, or if request fails.
    """
    api_key = getattr(settings, 'GEMINI_API_KEY', '')
    
    # If no API key or genai not installed, use offline rules
    if not HAS_GENAI or not api_key:
        logger.info("Using offline rule engine fallback (Gemini key not configured/installed).")
        return run_local_triage(symptoms_text)

    try:
        from google.genai import types
        from PIL import Image

        client = genai.Client(api_key=api_key)
        content_parts = [SYSTEM_PROMPT, f"User Symptoms:\n{symptoms_text}"]
        if image_path:
            try:
                content_parts.append(Image.open(image_path))
            except Exception as img_err:
                logger.error("Failed to load image for Gemini analysis: %s", img_err)

        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=content_parts,
            config=types.GenerateContentConfig(
                response_mime_type="application/json"
            )
        )
        response_text = response.text.strip()
        return json.loads(response_text)
    except Exception as exc:
        logger.error("Gemini API analysis failed: %s. Falling back to rule engine.", exc)
        return run_local_triage(symptoms_text)


CHAT_SYSTEM_PROMPT = """
You are Hero AI, a health-information companion for people in Nepal.
Reply in the same language as the user. If the user writes in Nepali, reply in
clear, natural Nepali (Devanagari). Be warm, brief, and practical.

This is NOT a diagnostic or prescribing service. Never name, confirm, rank, or
rule out a disease/condition, and do not tell the user what medicine, dose, or
treatment to take. Do not claim certainty. Instead, provide general wellbeing
information, safe next steps, and questions a qualified clinician may ask.

Always include a short reminder that you cannot diagnose and a clinician can
assess them. When symptoms could be an emergency (for example severe chest
pain, trouble breathing, stroke signs, severe bleeding, unconsciousness,
seizure, or immediate self-harm risk), clearly tell the person to call Nepal
ambulance 102 or go to the nearest emergency department now. Do not continue
with routine advice in that case. Never request passwords, financial details,
or unnecessary identifying information.
"""


def _local_chat_reply(message, language='en'):
    """Safe, useful fallback used when the generative service is unavailable."""
    text = message.lower()
    urgent_words = (
        'chest pain', 'trouble breathing', 'difficulty breathing', 'cannot breathe',
        'unconscious', 'seizure', 'stroke', 'heavy bleeding', 'suicide', 'self harm',
        'छाती दुख्ने', 'सास फेर्न गाह्रो', 'बेहोस', 'रक्तस्राव', 'आत्महत्या'
    )
    if any(word in text for word in urgent_words):
        if language == 'ne':
            return (
                'यो लक्षण आपतकालीन हुन सक्छ। अबेलम्ब एम्बुलेन्स १०२ मा कल गर्नुहोस् वा नजिकको आकस्मिक विभागमा जानुहोस्। '
                'म निदान गर्न सक्दिनँ।'
            )
        return (
            'These symptoms may need emergency care. Please call an ambulance on 102 in Nepal or go to the nearest emergency department now. '
            'I cannot diagnose this situation.'
        )
    if language == 'ne':
        return (
            'मैले तपाईंको चिन्ता बुझें। म निदान गर्न सक्दिनँ, तर सामान्य मार्गदर्शन दिन सक्छु। बिश्राम गर्नुहोस्, तुलनात्मक रूपमा पानी पिउनुहोस्, र लक्षण बढ्दै गए स्वास्थ्यकर्मीसँग सम्पर्क गर्नुहोस्। '
            'लक्षण कतिबेलादेखि छ र कति गम्भीर छ भन्नुहोस्।'
        )
    return (
        "I understand this can be worrying. I cannot diagnose, but I can offer general next steps. "
        "Rest, drink fluids as you normally can, and note when the symptoms began and whether they are worsening. "
        "Please contact a qualified clinician if they persist or concern you. How long has this been happening, and is it getting worse?"
    )


def get_health_chat_reply(message, language='en'):
    """Return medical guidance, with a private local fallback if Gemini is unavailable."""
    api_key = getattr(settings, 'GEMINI_API_KEY', '')
    if not HAS_GENAI or not api_key:
        return _local_chat_reply(message, language)

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemini-3.6-flash',
            contents=[
                CHAT_SYSTEM_PROMPT,
                f"Preferred response language: {'Nepali' if language == 'ne' else 'English'}.",
                f"User message: {message}",
            ]
        )
        reply = (response.text or '').strip()
        return reply or _local_chat_reply(message, language)
    except Exception as exc:
        logger.error("Gemini chat request failed: %s", exc)
        return _local_chat_reply(message, language)

