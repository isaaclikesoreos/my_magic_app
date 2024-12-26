from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from allauth.account.utils import send_email_confirmation
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.views import View
from django.views.generic import TemplateView, UpdateView, FormView, DeleteView
from django.contrib import messages
from .forms import ProfileForm, EmailForm
from .models import Profile


class ProfileView(LoginRequiredMixin, TemplateView):
    template_name = "a_users/profile.html"

    def get_context_data(self, **kwargs):
        username = self.kwargs.get("username")
        if username:
            profile = get_object_or_404(User, username=username).profile
        else:
            profile = self.request.user.profile
        return {"profile": profile}


class ProfileEditView(LoginRequiredMixin, UpdateView):
    model = Profile
    form_class = ProfileForm
    template_name = "a_users/profile_edit.html"

    def get_object(self):
        return self.request.user.profile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["onboarding"] = self.request.path == reverse_lazy("profile-onboarding")
        return context

    def get_success_url(self):
        return reverse_lazy("profile")


class ProfileSettingsView(LoginRequiredMixin, TemplateView):
    template_name = "a_users/profile_settings.html"


class ProfileEmailChangeView(LoginRequiredMixin, FormView):
    form_class = EmailForm
    template_name = "partials/email_form.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["instance"] = self.request.user
        return kwargs

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        if User.objects.filter(email=email).exclude(id=self.request.user.id).exists():
            messages.warning(self.request, f"{email} is already in use.")
        else:
            form.save()
            send_email_confirmation(self.request, self.request.user)
            messages.success(self.request, "Email updated and confirmation sent.")
        return redirect("profile-settings")


class ProfileEmailVerifyView(LoginRequiredMixin, View):
    def get(self, request):
        send_email_confirmation(request, request.user)
        messages.success(request, "Verification email sent.")
        return redirect("profile-settings")


class ProfileDeleteView(LoginRequiredMixin, DeleteView):
    model = User
    template_name = "a_users/profile_delete.html"
    success_url = reverse_lazy("home")

    def get_object(self):
        return self.request.user

    def form_valid(self, form):
        logout(self.request)
        messages.success(self.request, "Account deleted successfully.")
        return super().form_valid(form)
