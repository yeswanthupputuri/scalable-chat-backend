from .celery import app as celery_app

__all__ = ("celery_app",)

#Django --> config package --> __init__.py --> load celery application 
# so django and celery are now connected 