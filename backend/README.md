### Setup Environment

```bash
python -m venv env

source env/bin/activate
```

### Install dependancies

```bash
pip install -r requirements.txt
```

### API Keys Setup

Please create `.env` file from `.env.example` and fill in your API keys.

### Choose to use ContextualRAG or not:

> Note: ContextualRAG is a little bit expensive, so it's disabled by default.

Please set `use_contextual_rag` to `True` in [config.py](config.py) to use ContextualRAG.

### Database Setup

-   If you use ContextualRAG, run this:

```bash
docker compose -f contextual_rag_services.yml up -d
```

-   Otherwise, run this:

```bash
docker compose -f original_rag_services.yml up -d
```

### Run celery worker

```bash
celery -A src worker --loglevel=info
```

### Run backend server

```bash
python app.py
```
