from __future__ import annotations

from django.db import migrations

TASK_NAME = 'lead.task.task_collect_followups'


def create_collect_followups_schedule(apps, schema_editor):
    IntervalSchedule = apps.get_model('django_celery_beat', 'IntervalSchedule')
    PeriodicTask = apps.get_model('django_celery_beat', 'PeriodicTask')

    interval, _ = IntervalSchedule.objects.get_or_create(
        every=20,
        period='seconds',
    )

    PeriodicTask.objects.update_or_create(
        name=TASK_NAME,
        defaults={
            'interval': interval,
            'task': TASK_NAME,
            'enabled': True,
        },
    )


def remove_collect_followups_schedule(apps, schema_editor):
    PeriodicTask = apps.get_model('django_celery_beat', 'PeriodicTask')
    IntervalSchedule = apps.get_model('django_celery_beat', 'IntervalSchedule')

    try:
        task = PeriodicTask.objects.get(name=TASK_NAME)
    except PeriodicTask.DoesNotExist:
        return

    interval_id = task.interval_id
    task.delete()

    if interval_id:
        IntervalSchedule.objects.filter(id=interval_id, period='seconds', every=20).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('lead', '0001_initial')
    ]

    operations = [
        migrations.RunPython(create_collect_followups_schedule, remove_collect_followups_schedule),
    ]
