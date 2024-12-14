from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),  # Map '/home/' to the home view
]