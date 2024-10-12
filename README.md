# Knowledge Base Agent

## Database Diagram

![](./backend/public/knowledge_base.png)

## Run production

First, please fill in your API Keys and [Langfuse](https://cloud.langfuse.com/) keys in [.env.production](.env.production), then run:

```bash
cp .env.production .env
cp .env.production frontend/.env.local

docker compose up -d --build
```

Visit [http://localhost:3000](http://localhost:3000) to enjoy the app.

## Installation (dev)

-   [Running Backend server](./backend/README.md)
-   [Running Frontend server](./frontend/README.md)
