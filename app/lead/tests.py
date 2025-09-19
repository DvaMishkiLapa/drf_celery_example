import secrets
from datetime import timedelta

from django.test import TestCase, override_settings
from django.utils import timezone

from .models import Lead, LeadFollowup, LeadFollowupRule, LeadStatus
from .tasks import task_collect_followups


class CollectFollowupsTaskTest(TestCase):

    # Enables Celery's “eager” mode: tasks launched via task.delay() are executed immediately
    @override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
    def test_overdue_lead_enqueues_followup(self):
        # Generate a phone number until we find a value that does not collide with existing leads
        while True:
            # Keep format numeric and deterministic length
            phone_number = '79' + ''.join(str(secrets.randbelow(10)) for _ in range(8))
            if not Lead.objects.filter(phone=phone_number).exists():
                break

        lead = Lead.objects.create(phone=phone_number, status=LeadStatus.NEW)
        rule = LeadFollowupRule.objects.create(
            text='ping',
            status=LeadStatus.NEW,
            delay=1,
            is_enabled=True,
        )
        # Push the timestamp far enough back so the lead definitely exceeds the rule delay
        overdue_timestamp = timezone.now() - timedelta(minutes=rule.delay * 2)
        Lead.objects.filter(pk=lead.pk).update(updated_at=overdue_timestamp)

        result = task_collect_followups.delay()
        result.get(timeout=rule.delay + 1)  # Block until the eager Celery task finishes

        # Assert that a follow-up record was created for the overdue lead
        followup = LeadFollowup.objects.filter(lead=lead, rule=rule).first()
        self.assertIsNotNone(followup)
