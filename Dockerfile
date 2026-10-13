FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1

COPY pyproject.toml README.md LICENSE ./
COPY agents ./agents
COPY icu_multimodal ./icu_multimodal
COPY cli.py enrichment.py simulator.py icu_multimodal_app.py ./
RUN pip install --no-cache-dir .

RUN useradd --system --uid 10001 --no-create-home appuser
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)" || exit 1
CMD ["python", "cli.py", "serve", "--host", "0.0.0.0", "--port", "8000"]
