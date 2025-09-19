# leads/models.py
from __future__ import annotations

# from django.conf import settings
from django.db import models


class LeadStatus(models.TextChoices):
    NEW = 'new'
    SUBMITTED = 'submitted'
    VERIFIED = 'verified'
    PAID = 'paid'
    LOST = 'lost'


class Lead(models.Model):
    '''
    Current status of the lead with their details
    '''
    phone = models.CharField(max_length=32, unique=True)  # Keep phone numbers unique across leads.
    status = models.CharField(
        max_length=16, choices=LeadStatus.choices, default=LeadStatus.NEW
    )
    updated_at = models.DateTimeField(auto_now=True)  # Track when a lead was last touched for status analytics.

    class Meta:
        indexes = [
            models.Index(
                fields=['status'],
                name='lead_status_idx'
            ),  # Accelerate status-based lead lookups.
        ]


class LeadEvent(models.Model):
    '''
    History of changes in lead statuses
    '''
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='events')
    status = models.CharField(max_length=16, choices=LeadStatus.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    # created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        indexes = [
            models.Index(
                fields=['lead', '-created_at'],
                name='lead_event_latest_idx'
            ),  # Speed fetching the most recent event per lead.
        ]


class LeadFollowupRule(models.Model):
    '''
    Send text as a SMS followup to a lead's phone number
    if the lead's status didn't move to the next status
    after delay seconds from the previous status change
    '''

    text = models.CharField(max_length=140)
    status = models.CharField(max_length=16, choices=LeadStatus.choices)
    delay = models.PositiveSmallIntegerField()
    is_enabled = models.BooleanField(default=True)  # Toggle to disable followups without deleting the rule.

    class Meta:
        indexes = [
            models.Index(
                fields=['status', 'delay'],
                name='lead_rule_status_delay_idx'
            ),  # Fast rule selection when matching delay windows.
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['status', 'delay'],
                name='lead_rule_status_delay_uniq',
            ),  # Prevent duplicate followup delay rules per status.
        ]


class LeadFollowup(models.Model):
    '''
    Data on the timing of sending notifications
    '''
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='followups')
    rule = models.ForeignKey(
        LeadFollowupRule, on_delete=models.CASCADE, related_name='followups'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(
                fields=['lead', '-created_at'],
                name='lead_followup_history_idx'
            ),  # Speed timeline queries for followups per lead.
        ]
