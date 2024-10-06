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

### Monitoring (Optional)

Run this and open brower at port `5555` with `username = admin`, `password = admin123`

```bash
celery -A src flower --loglevel=info --basic-auth=admin:amdin123
```

### Run backend server

```bash
python app.py
```
