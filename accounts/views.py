from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from .forms import SeekerRegistrationForm, EmployerRegistrationForm, LoginForm


def register_seeker(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = SeekerRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f"Welcome, {user.username}! Your seeker account is ready.")
        return redirect('seeker_dashboard')
    return render(request, 'accounts/register_seeker.html', {'form': form})


def register_employer(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = EmployerRegistrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f"Welcome! Your employer account is ready.")
        return redirect('employer_dashboard')
    return render(request, 'accounts/register_employer.html', {'form': form})


def user_login(request):
    if request.user.is_authenticated:
        return redirect('home')
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        messages.success(request, f"Welcome back, {user.username}!")
        if user.is_seeker():
            return redirect('seeker_dashboard')
        else:
            return redirect('employer_dashboard')
    return render(request, 'accounts/login.html', {'form': form})


def user_logout(request):
    logout(request)
    messages.info(request, "You've been logged out.")
    return redirect('home')
