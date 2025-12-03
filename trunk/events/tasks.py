from celery import shared_task

from trunk.events.dispatcher import event_dispatcher


@shared_task
def dispatch_event_task(event_type, payload):
    """
    Celery task to dispatch events asynchronously.
    """
    # We call a special method on the dispatcher that knows it's running inside the task
    # and doesn't try to dispatch async again.
    event_dispatcher.dispatch_sync(event_type, payload)
