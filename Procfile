web: gunicorn webApp.wsgi --timeout 15 --workers 1 -c 8
worker: celery -A webApp worker --without-gossip --without-mingle --without-heartbeat -l info -c 8
