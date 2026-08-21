"""Safety-focused, session-friendly health guidance for Hero AI."""

import logging
import re

from django.conf import settings

from .services import HAS_GENAI, genai

logger = logging.getLogger(__name__)

MAX_CONTEXT_MESSAGES = 10
MAX_REPLY_LENGTH = 3000
SUPPORTED_LANGUAGES = {"en", "ne"}

SYSTEM_PROMPT = """
You are Hero AI, the health education and guidance assistant inside HeroHealth.
Provide concise, empathetic, practical general health information. You are not
a doctor and do not replace emergency or professional medical care.

Never diagnose, identify, confirm, rank, or rule out a disease. Never prescribe
medicines, provide doses, recommend starting/stopping prescription medicines,
or advise dangerous combinations. Do not claim to have examined the user or to
know their health records. Explain that several causes can be possible and that
a qualified clinician must evaluate the cause when relevant.

You may explain symptoms at a high level, prevention, nutrition, exercise,
general first aid, medication safety principles, terminology, and questions to
ask a clinician. Offer safe next steps and concise warning signs. If the user
describes a potentially urgent problem, direct them to immediate emergency care
instead of continuing a detailed conversation. For Nepal, the ambulance number
is 102. Do not invent phone numbers.

Reply in the requested language. For Nepali, use natural, understandable
Devanagari and retain an English medical term in parentheses when helpful.
Keep the response under 220 words unless the user specifically needs a short
checklist. Do not repeat a disclaimer in every sentence.
"""

EMERGENCY_TERMS = (
    "severe chest pain", "chest pressure", "difficulty breathing", "trouble breathing",
    "cannot breathe", "heavy bleeding", "loss of consciousness", "unconscious",
    "seizure", "stroke", "face drooping", "suicide", "self-harm", "self harm",
    "overdose", "poisoning", "severe allergic reaction", "anaphylaxis", "severe injury",
    "छातीमा धेरै दुखाइ", "सास फेर्न गाह्रो", "बेहोस", "दौरा", "रक्तस्राव", "आत्महत्या",
    "विषाक्त", "एलर्जी"
)


def resolve_language(message, requested_language):
    if requested_language not in SUPPORTED_LANGUAGES:
        requested_language = "en"
    return "ne" if re.search(r"[\u0900-\u097F]", message) else requested_language


def is_emergency_message(message):
    normalized = message.casefold()
    return any(term.casefold() in normalized for term in EMERGENCY_TERMS)


def emergency_reply(language):
    if language == "ne":
        return "यो आपतकालीन हुन सक्छ। अहिले नै नजिकको आपतकालीन विभागमा जानुहोस् वा नेपाल एम्बुलेन्स १०२ मा सम्पर्क गर्नुहोस्। यस अवस्थामा च्याटमा भर नपर्नुहोस्।"
    return "This may require urgent medical attention. Please go to the nearest emergency department now or contact Nepal Ambulance on 102. Do not rely on this chat for emergency treatment."


def unavailable_reply(language):
    if language == "ne":
        return "Hero AI अहिले अस्थायी रूपमा उपलब्ध छैन। कृपया केही समयपछि फेरि प्रयास गर्नुहोस्। आपतकालीन अवस्थामा तुरुन्त स्वास्थ्य सेवा लिनुहोस्।"
    return "Hero AI is temporarily unavailable. Please try again shortly. For urgent symptoms, seek professional medical care now."


def fallback_reply(language):
    if language == "ne":
        return "म सामान्य स्वास्थ्य जानकारी दिन सक्छु, तर रोगको निदान वा औषधि लेख्न सक्दिनँ। लक्षण कहिलेदेखि छ, कति गम्भीर छ, र के यसले दैनिक काममा असर गरेको छ भनेर बताउन सक्नुहुन्छ?"
    return "I can provide general health information, but I cannot diagnose or prescribe. When did this begin, how severe is it, and is it affecting your usual activities?"


def _context_for_model(history):
    context = []
    for item in history[-MAX_CONTEXT_MESSAGES:]:
        role = item.get("role")
        content = str(item.get("content", "")).strip()
        if role in {"user", "assistant"} and content:
            context.append(f"{role.title()}: {content[:MAX_REPLY_LENGTH]}")
    return "\n".join(context)


def generate_health_guidance(message, language, history):
    """Generate server-side guidance, falling back safely when Gemini is unavailable."""
    if is_emergency_message(message):
        return {"reply": emergency_reply(language), "is_emergency": True}

    api_key = getattr(settings, "GEMINI_API_KEY", "")
    if not HAS_GENAI or not api_key:
        return {"reply": fallback_reply(language), "is_emergency": False}

    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel("gemini-2.5-flash")
        prompt = (
            f"{SYSTEM_PROMPT}\n\nRequested response language: {'Nepali' if language == 'ne' else 'English'}\n"
            f"Recent conversation (may be empty):\n{_context_for_model(history)}\n\n"
            f"Current user message: {message}"
        )
        response = model.generate_content(prompt, request_options={"timeout": 15})
        reply = str(getattr(response, "text", "")).strip()
        if not reply:
            raise ValueError("Empty Gemini response")
        return {"reply": reply[:MAX_REPLY_LENGTH], "is_emergency": False}
    except Exception:
        logger.exception("Hero AI generation failed")
        return {"reply": fallback_reply(language), "is_emergency": False}
