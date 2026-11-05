import os

bind = f"0.0.0.0:{os.environ.get('APP_PORT', '8000')}"
workers = int(os.environ.get("GUNICORN_WORKERS", "2"))

accesslog = "-"
errorlog = "-"
timeout = 30