# Create your views here.
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django import forms
from .models import Profile
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm
from .forms import SignUpForm


'''
class ProfileForm(forms.Form):
    full_name = forms.CharField(max_length=120, required=False)
    student_id = forms.CharField(max_length=30, required=False)
    bio = forms.CharField(widget=forms.Textarea, required=False)
    

@login_required
def profile_view(request):
    profile, _ = Profile.objects.get_or_create(user=request.user)
    return render(request, "profile.html", {"profile": profile})

@login_required
def profile_edit(request):
    profile = request.user.profile

    if request.method == "POST":
        form = ProfileForm(request.POST)
        if form.is_valid():
            profile.full_name = form.cleaned_data["full_name"]
            profile.student_id = form.cleaned_data["student_id"]
            profile.bio = form.cleaned_data["bio"]
            profile.save()
            return redirect("profile")
    else:
        form = ProfileForm(initial={
            "full_name": profile.full_name,
            "student_id": profile.student_id,
            "bio": profile.bio,
        })

    return render(request, "profile_edit.html", {"form": form})



def signup(request):
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.email = form.cleaned_data["email"]
            user.save()
            login(request, user, backend="django.contrib.auth.backends.ModelBackend")
            return redirect("profile")
    else:
        form = SignUpForm()
    return render(request, "registration/signup.html", {"form": form})

    
    '''