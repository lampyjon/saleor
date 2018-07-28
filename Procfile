release: python manage.py migrate --no-input
web: uwsgi saleor/wsgi/uwsgi.ini
worker: celery worker --app=saleor
