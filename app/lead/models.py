from __future__ import annotations

# from django.conf import settings
from django.db import models


class LeadStatus(models.TextChoices):
    '''Authoritative list of lead states reused across models and tasks.'''

    NEW = 'new'
    SUBMITTED = 'submitted'
    VERIFIED = 'verified'
    PAID = 'paid'
    LOST = 'lost'


class Lead(models.Model):
    '''
    Current status of the lead with their details
    '''
    phone = models.CharField(max_length=32, unique=True)  # Deduplicate leads by phone, regardless of country format
    status = models.CharField(
        max_length=16, choices=LeadStatus.choices, default=LeadStatus.NEW
    )
    updated_at = models.DateTimeField(auto_now=True)  # Updated on every save: tasks use this to measure 'time stuck' in a status

    class Meta:
        indexes = [
            models.Index(
                fields=['status'],
                name='lead_status_idx'
            ),  # Accelerate queries that fetch all leads in a particular pipeline step
        ]


class LeadEvent(models.Model):
    '''
    History of changes in lead statuses
    '''
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='events')
    status = models.CharField(max_length=16, choices=LeadStatus.choices)  # Snapshot of the status right after the transition
    created_at = models.DateTimeField(auto_now_add=True)
    # created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    class Meta:
        indexes = [
            models.Index(
                fields=['lead', '-created_at'],
                name='lead_event_latest_idx'
            ),  # Support queries that grab 'latest event per lead' without table scans
        ]


class LeadFollowupRule(models.Model):
    '''
    Send text as a SMS followup to a lead's phone number
    if the lead's status didn't move to the next status
    after delay seconds from the previous status change
    '''

    text = models.CharField(max_length=140)
    status = models.CharField(max_length=16, choices=LeadStatus.choices)
    delay = models.PositiveSmallIntegerField()  # Minutes the lead may stay on the status before this followup is triggered
    is_enabled = models.BooleanField(default=True)  # Toggle to disable followups without deleting the rule

    class Meta:
        indexes = [
            models.Index(
                fields=['status', 'delay'],
                name='lead_rule_status_delay_idx'
            ),  # Fast rule selection when matching delay windows
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['status', 'delay'],
                name='lead_rule_status_delay_uniq',
            ),  # Prevent duplicate followup delay rules per status so scheduling logic stays deterministic
        ]


class LeadFollowup(models.Model):
    '''
    Data on the timing of sending notifications
    '''
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='followups')  # History for auditing which messages were sent to a lead
    rule = models.ForeignKey(
        LeadFollowupRule, on_delete=models.CASCADE, related_name='followups'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(
                fields=['lead', '-created_at'],
                name='lead_followup_history_idx'
            ),  # Speed timeline queries for followups per lead
        ]


class TaskExecutionLock(models.Model):
    name = models.CharField(max_length=128, unique=True)
    locked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['name']),
        ]
