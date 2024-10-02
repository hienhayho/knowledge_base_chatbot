import os
from dotenv import load_dotenv
from src.database import DatabaseManager
from src.database.sql_model import Users
from src.tasks import parse_document
from celery.result import AsyncResult

load_dotenv()

task = parse_document.delay("sample/dummy.csv")
print(task.id)

while True:
    result = AsyncResult(task.id)
    print(result.state)
    print(result.info)
    if result.state == "SUCCESS":
        break
