from datetime import timedelta
import os

static_dir = os.getenv('OPENSHIFT_DATA_DIR', os.path.dirname(__file__))
static_dir = os.path.join(static_dir, 'static')

CELERYBEAT_SCHEDULE = {
    'importtweets-task': {
        'task': 'stalkr.tasks.import_tweets',
        'schedule': timedelta(minutes=50)
    },
    'computepagerank-task': {
        'task': 'stalkr.tasks.compute_pagerank',
        'schedule': timedelta(minutes=70)
    },
}

CELERY_TIMEZONE = 'UTC'
