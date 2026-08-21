from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name='home'),
    path('consultation/', views.consultation_view, name='consultation'),
    path('result/<int:pk>/', views.consultation_result_view, name='consultation_result'),
    path('emergency/', views.emergency_view, name='emergency'),
]
