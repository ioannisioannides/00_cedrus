"""
Views for Complaints and Appeals.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import CreateView, ListView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.shortcuts import redirect

from audits.models import Complaint, Appeal
from audits.complaint_forms import ComplaintForm, AppealForm
from trunk.services.complaint_service import ComplaintService

class ComplaintListView(LoginRequiredMixin, ListView):
    model = Complaint
    template_name = "audits/complaint_list.html"
    context_object_name = "complaints"

    def get_queryset(self):
        # In a real app, filter by permissions
        return Complaint.objects.all().order_by("-submitted_at")

class ComplaintCreateView(LoginRequiredMixin, CreateView):
    model = Complaint
    form_class = ComplaintForm
    template_name = "audits/complaint_form.html"
    success_url = reverse_lazy("audits:complaint_list")

    def form_valid(self, form):
        self.object = ComplaintService.create_complaint(form.cleaned_data, self.request.user)
        messages.success(self.request, "Complaint submitted successfully.")
        return redirect(self.get_success_url())

class ComplaintDetailView(LoginRequiredMixin, DetailView):
    model = Complaint
    template_name = "audits/complaint_detail.html"
    context_object_name = "complaint"

class AppealListView(LoginRequiredMixin, ListView):
    model = Appeal
    template_name = "audits/appeal_list.html"
    context_object_name = "appeals"

    def get_queryset(self):
        return Appeal.objects.all().order_by("-submitted_at")

class AppealCreateView(LoginRequiredMixin, CreateView):
    model = Appeal
    form_class = AppealForm
    template_name = "audits/appeal_form.html"
    success_url = reverse_lazy("audits:appeal_list")

    def form_valid(self, form):
        self.object = ComplaintService.create_appeal(form.cleaned_data, self.request.user)
        messages.success(self.request, "Appeal submitted successfully.")
        return redirect(self.get_success_url())

class AppealDetailView(LoginRequiredMixin, DetailView):
    model = Appeal
    template_name = "audits/appeal_detail.html"
    context_object_name = "appeal"
