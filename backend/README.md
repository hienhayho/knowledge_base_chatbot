### Setup Environment

**IMPORTANT**: Please use `python==3.12` to prevent any unexpected behaviors.

```bash
python -m venv env

source env/bin/activate
```

### Install dependancies

```bash
pip install -r requirements.txt

bash scripts/nltk_download.sh
```

### API Keys Setup

Please copy `.env` file from `.env.example` and fill in required API keys.

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
