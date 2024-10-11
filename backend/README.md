### Setup Environment

**IMPORTANT**: Please use `python >= 3.11` to prevent any unexpected behaviors.

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

Please create `.env` file from `.env.example` and fill in all API keys below.

|         NAME          |                     Where to get ?                      |
| :-------------------: | :-----------------------------------------------------: |
|   `OPENAI_API_KEY`    | [OpenAI Platform](https://platform.openai.com/api-keys) |
| `LLAMA_PARSE_API_KEY` |    [LlamaCloud](https://cloud.llamaindex.ai/api-key)    |
|   `COHERE_API_KEY`    |     [Cohere](https://dashboard.cohere.com/api-keys)     |
| `LANGFUSE_SECRET_KEY` |      [LangfuseCloud](https://cloud.langfuse.com/)       |
| `LANGFUSE_PUBLIC_KEY` |      [LangfuseCloud](https://cloud.langfuse.com/)       |
|    `LANGFUSE_HOST`    |      [LangfuseCloud](https://cloud.langfuse.com/)       |

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
