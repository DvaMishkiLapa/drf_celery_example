import logging
from datetime import timedelta
from time import sleep

from celery import shared_task
from django.db.models import (DurationField, Exists, ExpressionWrapper, F,
                              OuterRef, Value)
from django.db.models.functions import Now
from lead import models

logger = logging.getLogger('app')


def send_sms(phone: str, text: str):
    '''Sends an SMS to a phone number'''
    sleep(3)
    logger.debug(f'send_sms: {phone}: {text}')


@shared_task(name='lead.task.task_collect_followups')
def task_collect_followups():
    '''Find leads stalled in a status beyond rule delays and enqueue followups.'''
    # Translate rule.delay minutes into a database-level timedelta for filtering
    # Can't use timedelta(minutes=F('delay')): F('delay') is a database reference, while timedelta expects a plain number :(
    delay_interval = ExpressionWrapper(F('delay') * Value(timedelta(minutes=1)), output_field=DurationField())

    # Build a subquery that returns ids of leads whose updated_at exceeds the rule delay
    # and that have not already received a follow-up for the same rule since the last status change
    lead_candidates = models.Lead.objects.annotate(
        elapsed=ExpressionWrapper(
            Now() - F('updated_at'),
            output_field=DurationField(),
        )
    ).filter(
        status=OuterRef('status'),  # Match only leads sharing the rule status
        elapsed__gte=OuterRef('delay_interval'),  # Keep leads that exceeded the rule delay
    ).exclude(
        Exists(
            models.LeadFollowup.objects.filter(
                lead_id=OuterRef('id'),
                rule_id=OuterRef('pk'),
                created_at__gte=OuterRef('updated_at'),  # Avoid resending since the last status change
            )
        )
    ).values_list('id', flat=True)

    payload = []  # Accumulate (lead_id, rule_id) pairs for Celery starmap.
    # Iterate over rules that are currently active and have at least one matching lead.
    eligible_rules = (
        models.LeadFollowupRule.objects.filter(is_enabled=True)
        .annotate(delay_interval=delay_interval)
        .filter(Exists(lead_candidates))  # Keep only rules that actually have pending leads.
        .values_list('id', 'status', 'delay_interval')
    )

    for rule_id, status, delay_span in eligible_rules:
        # Recompute stalled leads with the resolved delay to avoid reusing an outdated annotated value.
        stalled_leads = (
            models.Lead.objects.annotate(
                elapsed=ExpressionWrapper(
                    Now() - F('updated_at'),
                    output_field=DurationField(),
                )
            )
            .filter(
                status=status,
                elapsed__gte=delay_span,
            )
            .exclude(
                Exists(
                    models.LeadFollowup.objects.filter(
                        lead_id=OuterRef('id'),
                        rule_id=rule_id,
                        created_at__gte=OuterRef('updated_at'),
                    )
                )
            )
            .values_list('id', flat=True)
        )
        payload.extend((lead_id, rule_id) for lead_id in stalled_leads)

    if payload:
        # More convenient than delay for every task
        task_send_followup.starmap(payload).apply_async()


@shared_task(name='lead.task.task_send_followup')
def task_send_followup(lead_id: int, rule_id: int):
    '''Sends a followup to a lead'''
    logger.debug(f'task_send_followup: {lead_id}; {rule_id}')
    lead_followup_payload = models.LeadFollowup.objects.create(
        lead_id=lead_id,
        rule_id=rule_id
    )
    send_sms(phone=lead_followup_payload.lead.phone, text=lead_followup_payload.rule.text)
