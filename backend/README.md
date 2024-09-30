# Python Environment Setup with Celery, Qdrant, and Redis

## Setup

- Python 3.7+
- Docker (optional but recommended)

## 1. **Create a virtual environment:**

```bash
python -m venv .venv
source .venv/bin/activate
```

## 2. **Install dependencies:**

```bash
pip install -r requirements.txt
```

## 3. **Set up Redis**

make sure redis is running in your system

## 4. **Set up Qdrant**

First, download the latest Qdrant image from Dockerhub:

```bash
docker pull qdrant/qdrant
```

Then, run the service:

```bash
docker run -p 6333:6333 -p 6334:6334 \
    -v $(pwd)/qdrant_storage:/qdrant/storage:z \
    qdrant/qdrant
```

## Start the app

In separate terminal, run the follow command

Start celeray

```bash
celery -A src worker --loglevel=info
```

Start flower

```bash
celery -A src flower --loglevel=info
```

Start FastAPI

```
uvicorn app:app
```
