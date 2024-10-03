## Installation

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

### Database Setup

```bash
docker compose up -d
```

### Run celery worker

```bash
celery -A src worker --loglevel=info
```

### Run backend server

```bash
python app.py
```
