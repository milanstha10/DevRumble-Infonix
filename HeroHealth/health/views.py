import json
import time

from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.http import require_GET, require_POST
from django.contrib import messages
from .models import Consultation
from .forms import ConsultationForm
from ai_engine.safety import is_safe_query, clean_query_text
from ai_engine.chat import MAX_CONTEXT_MESSAGES, generate_health_guidance, resolve_language
from ai_engine.services import analyze_symptoms_ai

CHAT_HISTORY_KEY = 'hero_ai_chat_history'
CHAT_HISTORY_USER_KEY = 'hero_ai_chat_user_id'
CHAT_MESSAGE_LIMIT = 1200
CHAT_RATE_LIMIT = 12
CHAT_RATE_WINDOW_SECONDS = 60

def home_view(request):
    return render(request, 'home/home.html')

def consultation_view(request):
    if request.method == 'POST':
        form = ConsultationForm(request.POST, request.FILES)
        if form.is_valid():
            # Validate input first
            symptoms_text = form.cleaned_data.get('symptoms', '')
            is_safe, error_msg = is_safe_query(symptoms_text)
            if not is_safe:
                messages.error(request, error_msg)
                return render(request, 'health/consultation.html', {'form': form})

            # Create record and save image if uploaded
            consultation = form.save(commit=False)
            if request.user.is_authenticated:
                consultation.user = request.user
            consultation.save()

            # Clean and trigger AI Engine
            clean_text = clean_query_text(symptoms_text)
            image_path = consultation.image.path if consultation.image else None
            
            ai_response = analyze_symptoms_ai(clean_text, image_path)
            
            # Save results
            consultation.result_json = ai_response
            consultation.save()

            return redirect('consultation_result', pk=consultation.pk)
        else:
            messages.error(request, "Failed to submit symptoms. Please try again.")
    else:
        form = ConsultationForm()
        
    return render(request, 'health/consultation.html', {'form': form})

def consultation_result_view(request, pk):
    consultation = get_object_or_404(Consultation, pk=pk)
    
    # Simple check to protect patient confidentiality:
    # If the consultation belongs to a user, only allow that user to view it
    if consultation.user and consultation.user != request.user:
        messages.error(request, "You do not have permission to view this report.")
        return redirect('home')

    result = consultation.result_json or {}
    
    # We can pass the probable causes, recommended actions, safety warnings, etc.
    context = {
        'consultation': consultation,
        'result': result,
        'severity': result.get('severity', 'Low'),
        'disclaimer': result.get('disclaimer', ''),
        'causes': result.get('probable_causes', []),
        'actions': result.get('recommended_actions', []),
        'specialty': result.get('suggested_specialty', 'General Medicine'),
        'alert': result.get('urgency_alert', '')
    }
    return render(request, 'health/result.html', context)

def emergency_view(request):
    helplines = [
        {"name": "Nepal Red Cross Ambulance", "number": "102", "desc": "Ambulance service across major towns in Nepal"},
        {"name": "Nepal Police Emergency", "number": "100", "desc": "Emergency police dispatch and safety reports"},
        {"name": "Nepal Fire Brigade", "number": "101", "desc": "Fire control and search and rescue"},
        {"name": "Traffic Police Control", "number": "103", "desc": "Highway emergency or traffic accident assistance"},
        {"name": "Mental Health Hotline", "number": "1166", "desc": "Government-operated suicide prevention and mental health support"},
        {"name": "Child Helpline Nepal", "number": "1098", "desc": "Child protection and rescue coordination services"},
        {"name": "Bir Hospital Emergency", "number": "01-4221804", "desc": "Emergency ward, Kantipath, Kathmandu"},
        {"name": "TUTH Maharajgunj Emergency", "number": "01-4412505", "desc": "Teaching Hospital Emergency ward, Kathmandu"},
        {"name": "Patan Hospital Emergency", "number": "01-5521048", "desc": "Lagankhel, Lalitpur emergency desk"},
        {"name": "Nepal Red Cross Blood Bank", "number": "01-4272761", "desc": "Emergency blood supply search and collection center"}
    ]
    return render(request, 'health/emergency.html', {'helplines': helplines})


@login_required
def chatbot_view(request):
    """Private, session-scoped Hero AI experience."""
    return render(request, 'health/chatbot.html')


@login_required
@require_POST
def chatbot_message_view(request):
    try:
        data = json.loads(request.body)
    except (TypeError, json.JSONDecodeError):
        return JsonResponse({'error': 'Please send a valid message.'}, status=400)

    if not isinstance(data, dict):
        return JsonResponse({'success': False, 'error': 'Please send a valid message.'}, status=400)

    message = clean_query_text(str(data.get('message', '')))
    if not message:
        return JsonResponse({'success': False, 'error': 'Please enter a message before sending.'}, status=400)
    if len(message) > CHAT_MESSAGE_LIMIT:
        return JsonResponse({'success': False, 'error': f'Please keep messages under {CHAT_MESSAGE_LIMIT} characters.'}, status=400)
    if not _within_chat_rate_limit(request):
        return JsonResponse({'success': False, 'error': 'You are sending messages too quickly. Please wait a moment and try again.'}, status=429)

    language = resolve_language(message, data.get('language', 'en'))
    history = _get_chat_history(request)
    result = generate_health_guidance(message, language, history)
    _save_chat_history(request, history + [
        {'role': 'user', 'content': message},
        {'role': 'assistant', 'content': result['reply']},
    ])
    return JsonResponse({
        'success': True,
        'reply': result['reply'],
        'language': language,
        'is_emergency': result['is_emergency'],
    })


@login_required
@require_GET
def chatbot_history_view(request):
    return JsonResponse({'success': True, 'messages': _get_chat_history(request)})


@login_required
@require_POST
def chatbot_reset_view(request):
    request.session.pop(CHAT_HISTORY_KEY, None)
    request.session[CHAT_HISTORY_USER_KEY] = request.user.pk
    request.session.modified = True
    return JsonResponse({'success': True})


def _get_chat_history(request):
    """Keep temporary conversation data private to this authenticated session/user."""
    if request.session.get(CHAT_HISTORY_USER_KEY) != request.user.pk:
        request.session[CHAT_HISTORY_KEY] = []
        request.session[CHAT_HISTORY_USER_KEY] = request.user.pk
        request.session.modified = True
    history = request.session.get(CHAT_HISTORY_KEY, [])
    return history if isinstance(history, list) else []


def _save_chat_history(request, history):
    request.session[CHAT_HISTORY_KEY] = history[-MAX_CONTEXT_MESSAGES:]
    request.session[CHAT_HISTORY_USER_KEY] = request.user.pk
    request.session.modified = True


def _within_chat_rate_limit(request):
    if not request.session.session_key:
        request.session.save()
    key = f'hero-ai-rate:{request.user.pk}:{request.session.session_key}'
    now = time.time()
    attempts = [stamp for stamp in cache.get(key, []) if now - stamp < CHAT_RATE_WINDOW_SECONDS]
    if len(attempts) >= CHAT_RATE_LIMIT:
        cache.set(key, attempts, timeout=CHAT_RATE_WINDOW_SECONDS)
        return False
    attempts.append(now)
    cache.set(key, attempts, timeout=CHAT_RATE_WINDOW_SECONDS)
    return True
