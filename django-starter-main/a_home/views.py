from django.shortcuts import render
from django.contrib.auth.decorators import login_required

@login_required
def home(request):
    context = {
        'user': request.user,  # Pass the logged-in user to the template
    }
    return render(request, 'home.html', context)