# leads/models.py
from __future__ import annotations

from django.conf import settings
from django.db import models


class LeadStatus(models.TextChoices):
    NEW = "new"
    SUBMITTED = "submitted"
    VERIFIED = "verified"
    PAID = "paid"
    LOST = "lost"


class Lead(models.Model):
    phone = models.CharField(max_length=32)
    status = models.CharField(
        max_length=16, choices=LeadStatus.choices, default=LeadStatus.NEW
    )


class LeadEvent(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="events")
    status = models.CharField(max_length=16, choices=LeadStatus.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)


class LeadFollowupRule(models.Model):
    """
    Send text as a SMS followup to a lead's phone number
    if the lead's status didn't move to the next status
    after delay seconds from the previous status change
    """

    text = models.CharField(max_length=140)
    status = models.CharField(max_length=16, choices=LeadStatus.choices)
    delay = models.PositiveSmallIntegerField()


class LeadFollowup(models.Model):
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name="followups")
    rule = models.ForeignKey(
        LeadFollowupRule, on_delete=models.CASCADE, related_name="followups"
    )
    created_at = models.DateTimeField(auto_now_add=True)
