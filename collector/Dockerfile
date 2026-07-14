FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt ./
COPY wheels /wheels
RUN if [ -d /wheels ] && [ "$(ls -A /wheels)" ]; then \
    pip install --no-cache-dir --no-index --find-links /wheels -r requirements.txt; \
  else \
    pip install --no-cache-dir -r requirements.txt; \
  fi

COPY collector.py ./collector.py

CMD ["python", "collector.py"]
