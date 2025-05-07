from django.shortcuts import render, redirect
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.views import generic
from django.views.decorators.csrf import ensure_csrf_cookie
from django.http import HttpResponseNotAllowed
from .forms import SignUpForm

def signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request, user)
            return redirect('job_list')
    else:
        form = SignUpForm()
    return render(request, 'accounts/signup.html', {'form': form})

@login_required
def profile(request):
    return render(request, 'accounts/profile.html')

def logout_view(request):
    """
    Custom logout view that only allows POST method for security
    and redirects to the login page after logout.
    
    This ensures protection against CSRF attacks by preventing
    logout via GET requests from malicious sites.
    """
    if request.method == 'POST':
        logout(request)
        return redirect('login')
    return HttpResponseNotAllowed(['POST'], 'Logout requires POST method')
