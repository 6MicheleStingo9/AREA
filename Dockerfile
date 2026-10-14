# The web interface (frontend/), built with Node: only the build reaches the final image
FROM node:22-slim AS web

WORKDIR /src/frontend
# The packages first, so that a change to the code alone does not install them again
COPY frontend/package.json frontend/package-lock.json frontend/.npmrc ./
COPY frontend/ui/package.json ui/
COPY frontend/web/package.json web/
RUN npm ci
COPY frontend/ ./
# The strings and the logo, which the build reads from outside frontend/
COPY locales/ /src/locales/
COPY files/img/brand/ /src/files/img/brand/
RUN npm run build


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
COPY --from=web /src/frontend/web/dist frontend/web/dist

# Smoke test: verify pyswip can load libswipl at build time
RUN python -c "from pyswip import Prolog; Prolog()"

EXPOSE 8000

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
