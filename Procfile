web: gunicorn webApp.wsgi
worker: celery -A webApp worker --without-gossip --without-mingle --without-heartbeat -l info
