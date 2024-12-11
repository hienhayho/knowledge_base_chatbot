ARG VERSION

FROM python:${VERSION:-3.11}

WORKDIR /app

COPY requirements.txt .

COPY scripts/nltk_download.sh ./scripts/nltk_download.sh

RUN pip install --no-cache-dir -r requirements.txt \
    && chmod +x ./scripts/nltk_download.sh && bash ./scripts/nltk_download.sh


EXPOSE 8000

COPY . .
