FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY ./requirements.lock /app
RUN sed '/-e/d' requirements.lock > requirements.txt
RUN pip install -r requirements.txt

RUN pip install --no-cache-dir --upgrade -r /app/requirements.txt

COPY ./src/pyipam /app/pyipam

CMD ["uvicorn", "pyipam.main:app", "--host", "0.0.0.0", "--port", "80"]
