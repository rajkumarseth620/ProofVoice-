web: python backend/manage.py migrate && python backend/manage.py collectstatic --noinput && gunicorn --chdir backend config.wsgi:application --bind 0.0.0.0:$PORT
