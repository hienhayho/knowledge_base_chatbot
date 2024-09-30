from celery import Celery

celery = Celery('document_parser', 
                broker='redis://localhost:6379/0',
                include=[
                    "src.tasks.document_parser_tasks",
                ])

# Optional: Configure Celery
celery.conf.update(
    result_backend='redis://localhost:6379/0',
    task_serializer='json',
    result_serializer='json',
    accept_content=['json'],
    timezone='UTC',
    enable_utc=True,
)