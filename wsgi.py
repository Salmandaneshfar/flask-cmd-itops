from app import app

# Expose the Flask app for WSGI servers (gunicorn/uwsgi)
application = app


