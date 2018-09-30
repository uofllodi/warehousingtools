web: gunicorn webApp.wsgi --timeout 20
worker: celery -A webApp worker --without-gossip --without-mingle --without-heartbeat -l info
