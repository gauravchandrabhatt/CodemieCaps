FROM python:3.12-slim
WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
COPY web ./web
RUN pip install --no-cache-dir .
ENV CODIEMIE_DATABASE_URL=sqlite:////data/codemiecaps.db
EXPOSE 8000
CMD ["uvicorn", "codemie_caps.main:app", "--host", "0.0.0.0", "--port", "8000"]
