ARG VERSION

FROM python:${VERSION:-3.11}

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .
