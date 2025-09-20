import logging
from contextlib import contextmanager
from datetime import timedelta
from functools import wraps
from typing import Callable, TypeVar

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from lead.models import TaskExecutionLock

logger = logging.getLogger(__name__)

T = TypeVar('T')


@contextmanager
def _db_task_lock(name: str, timeout: timedelta):
    with transaction.atomic():
        # Grab a row-level lock so concurrent workers serialize on the same TaskExecutionLock record
        lock, _ = TaskExecutionLock.objects.select_for_update().get_or_create(name=name)
        now = timezone.now()
        if lock.locked_at is None or (now - lock.locked_at) > timeout:
            lock.locked_at = now
            lock.save(update_fields=['locked_at'])
            try:
                yield True
            finally:
                lock.locked_at = None
                lock.save(update_fields=['locked_at'])
        else:
            yield False


def singleton_task(lock_name: str, timeout: timedelta | None = None):
    timeout = timeout or timedelta(seconds=settings.TASK_LOCK_TIMEOUT)

    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs):
            with _db_task_lock(lock_name, timeout) as acquired:
                if not acquired:
                    logger.debug('Task %s skipped: lock %s is held', lock_name, lock_name)
                    return None
                # Only the worker that successfully acquired the lock proceeds to execute the task body
                return func(*args, **kwargs)

        return wrapper

    return decorator
