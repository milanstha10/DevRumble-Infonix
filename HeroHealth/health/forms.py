from django import forms
from .models import Consultation

class ConsultationForm(forms.ModelForm):
    class Meta:
        model = Consultation
        fields = ['symptoms', 'image']
        widgets = {
            'symptoms': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 5,
                'placeholder': 'Type your symptoms here... E.g., I have a high fever of 101F since yesterday, slight dry cough, and mild body aches.'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control-file',
                'accept': 'image/*'
            })
        }
