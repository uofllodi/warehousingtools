from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'webApp.settings')

app = Celery('webApp',
             #broker='pyamqp://guest@localhost//',
             broker="amqp://wdkkpikj:IaoV-f8L_2SlD7yTxeegPX4b1oIqNms9@wasp.rmq.cloudamqp.com/wdkkpikj",
             backend='rpc://',
             broker_pool_limit=1,
             )

app.conf.update(
             broker_pool_limit=1,
             broker_heartbeat=None,
             broker_connection_timeout=30,  # May require a long timeout due to Linux DNS timeouts etc
             event_queue_expires=60,  # Will delete all celeryev. queues without consumers after 1 minute.
             worker_prefetch_multiplier=1,  # Disable prefetching, it's causes problems and doesn't help performance
             worker_concurrency=8,
             )

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# namespace='CELERY' means all celery-related configuration keys
# should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.task(bind=True)
def debug_task(self):
    print('Request: {0!r}'.format(self.request))
