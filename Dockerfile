FROM python:3.11-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends swi-prolog && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# CPU-only PyTorch for the local causal classifier (Laya), first: the default wheels pull in CUDA
RUN pip install --no-cache-dir --index-url https://download.pytorch.org/whl/cpu torch==2.14.1

COPY requirements.txt requirements-laya.txt ./
RUN pip install --no-cache-dir -r requirements.txt -r requirements-laya.txt

COPY . .

# Smoke test: verify pyswip can load libswipl at build time
RUN python -c "from pyswip import Prolog; Prolog()"

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
