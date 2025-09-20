import random
from datetime import timedelta
from threading import Event, Thread
from unittest.mock import patch

from django.test import TestCase, override_settings
from django.utils import timezone

from .models import (Lead, LeadFollowup, LeadFollowupRule, LeadStatus,
                     TaskExecutionLock)
from .tasks import task_collect_followups, task_send_followup


def _get_random_phone_number() -> str:
    return f'+{str(random.randint(10_000_000, 99_999_999))}'


class CollectFollowupsTaskTest(TestCase):

    # Enables Celery's eager mode: tasks launched via task.delay() are executed immediately
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
        # Prime a followup within the repeat threshold so the task must skip re-sending
        LeadFollowup.objects.create(lead=lead, rule=rule, created_at=timezone.now())

        with self.assertLogs('app', level='DEBUG') as log_capture:
            task_send_followup(lead_id=lead.id, rule_id=rule.id)

        self.assertTrue(any('Skip followup' in message for message in log_capture.output))
        self.assertEqual(LeadFollowup.objects.filter(lead=lead, rule=rule).count(), 1)

    @override_settings(CELERY_TASK_ALWAYS_EAGER=True, CELERY_TASK_EAGER_PROPAGATES=True)
    def test_reenqueue_after_repeat_threshold(self):
        phone_number = _get_random_phone_number()
        lead = Lead.objects.create(phone=phone_number, status=LeadStatus.NEW)
        rule = LeadFollowupRule.objects.create(text='ping', status=LeadStatus.NEW, delay=1, is_enabled=True)

        overdue_timestamp = timezone.now() - timedelta(minutes=rule.delay * 4)
        Lead.objects.filter(pk=lead.pk).update(updated_at=overdue_timestamp)

        initial_followup = LeadFollowup.objects.create(lead=lead, rule=rule)
        LeadFollowup.objects.filter(pk=initial_followup.pk).update(
            created_at=overdue_timestamp + timedelta(minutes=rule.delay)
        )

        with patch('lead.tasks.FOLLOWUP_REPEAT_THRESHOLD', timedelta(minutes=1)):
            payload = task_collect_followups.delay()
            payload.get(timeout=2)

        self.assertEqual(LeadFollowup.objects.filter(lead=lead, rule=rule).count(), 2)

    def test_collect_followups_locked_execution(self):
        release_event = Event()
        entered_event = Event()
        second_entered_event = Event()
        call_counter = {'value': 0}

        def blocking_collect():
            call_counter['value'] += 1
            if call_counter['value'] == 1:
                entered_event.set()
                release_event.wait()  # Keep the first task on the lock until the test explicitly frees it
            else:
                second_entered_event.set()  # The contender should only reach here after the lock is released
            return []

        with patch('lead.tasks._collect_simple_followups', side_effect=blocking_collect):
            worker = Thread(target=task_collect_followups)
            contender = None
            worker.start()

            try:
                self.assertTrue(entered_event.wait(timeout=1))  # Ensure the first task holds the lock before spawning contender
                contender = Thread(target=task_collect_followups)
                contender.start()

                self.assertFalse(second_entered_event.wait(timeout=0.2))  # Contender must not pass the lock until we release it
            finally:
                release_event.set()
                worker.join(timeout=5)
                if contender is not None:
                    contender.join(timeout=5)

        self.assertFalse(worker.is_alive())
        self.assertIsNotNone(contender)
        self.assertFalse(contender.is_alive())
        self.assertTrue(second_entered_event.is_set())

        lock = TaskExecutionLock.objects.get(name='lead.task.task_collect_followups')
        self.assertIsNone(lock.locked_at)
        print(f'TaskExecutionLock used for blocking: id={lock.id}, name={lock.name}')
