FROM python:3.9.16-bullseye
WORKDIR /app
COPY requirements.txt /app/
ENV PATH=/app/.local/bin:$PATH
RUN pip install --no-cache-dir -r requirements.txt
COPY ./. /app/
