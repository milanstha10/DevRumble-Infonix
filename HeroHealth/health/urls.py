from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('consultation/', views.consultation_view, name='consultation'),
    path('result/<int:pk>/', views.consultation_result_view, name='consultation_result'),
    path('emergency/', views.emergency_view, name='emergency'),
    path('chat/', views.chatbot_view, name='chatbot'),
    path('chat/api/message/', views.chatbot_message_view, name='chatbot_message'),
    path('chat/api/history/', views.chatbot_history_view, name='chatbot_history'),
    path('chat/api/reset/', views.chatbot_reset_view, name='chatbot_reset'),
]
