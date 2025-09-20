import random
from datetime import timedelta

from django.test import TestCase, override_settings
from django.utils import timezone

from .models import Lead, LeadFollowup, LeadFollowupRule, LeadStatus
from .tasks import task_collect_followups, task_send_followup


def _get_random_phone_number() -> str:
    return f'+{str(random.randint(10_000_000, 99_999_999))}'


class CollectFollowupsTaskTest(TestCase):

    # Enables Celery's “eager” mode: tasks launched via task.delay() are executed immediately
    @override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
    def test_overdue_lead_enqueues_followup(self):
        phone_number = _get_random_phone_number()
        lead = Lead.objects.create(phone=phone_number, status=LeadStatus.NEW)
        rule = LeadFollowupRule.objects.create(text='ping', status=LeadStatus.NEW, delay=1, is_enabled=True)
        # Push the timestamp far enough back so the lead definitely exceeds the rule delay
        overdue_timestamp = timezone.now() - timedelta(minutes=rule.delay * 2)
        Lead.objects.filter(pk=lead.pk).update(updated_at=overdue_timestamp)

        result = task_collect_followups.delay()
        result.get(timeout=rule.delay + 1)  # Block until the eager Celery task finishes

        # Assert that a follow-up record was created for the overdue lead
        followup = LeadFollowup.objects.filter(lead=lead, rule=rule).first()
        self.assertIsNotNone(followup)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
    def test_disabled_rule_skips_followup(self):
        phone_number = _get_random_phone_number()
        lead = Lead.objects.create(phone=phone_number, status=LeadStatus.NEW)
        # Disabled rule should be ignored even though delay and status match
        rule = LeadFollowupRule.objects.create(text='ping', status=LeadStatus.NEW, delay=1, is_enabled=False)
        overdue_timestamp = timezone.now() - timedelta(minutes=rule.delay * 2)
        Lead.objects.filter(pk=lead.pk).update(updated_at=overdue_timestamp)

        result = task_collect_followups.delay()
        result.get(timeout=rule.delay + 1)

        self.assertFalse(LeadFollowup.objects.filter(lead=lead, rule=rule).exists())

    def test_skip_recent_followup(self):
        phone_number = _get_random_phone_number()
        lead = Lead.objects.create(phone=phone_number, status=LeadStatus.NEW)
        rule = LeadFollowupRule.objects.create(text='ping', status=LeadStatus.NEW, delay=1, is_enabled=True)
        LeadFollowup.objects.create(lead=lead, rule=rule, created_at=timezone.now())

        with self.assertLogs('app', level='DEBUG') as log_capture:
            task_send_followup(lead_id=lead.id, rule_id=rule.id)

        self.assertTrue(any('Skip followup' in message for message in log_capture.output))
        self.assertEqual(LeadFollowup.objects.filter(lead=lead, rule=rule).count(), 1)
