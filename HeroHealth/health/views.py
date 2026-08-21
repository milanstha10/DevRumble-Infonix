from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Consultation
from .forms import ConsultationForm
from ai_engine.safety import is_safe_query, clean_query_text
from ai_engine.services import analyze_symptoms_ai

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
