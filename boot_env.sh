#!/usr/bin/env bash
set -e

echo "🚀 Inicializando ambiente do pod_ffmpeg..."
cd /workspace/pod_ffmpeg

# Atualiza o repositório (se estiver versionado)
git pull || true

# Ativa o venv
source /workspace/venv/bin/activate

# Sobe a API em background e salva log
mkdir -p /workspace/logs
nohup uvicorn app:app --host 0.0.0.0 --port 8090 --reload  > /workspace/logs/api.log 2>&1 &

echo "✅ Servidor iniciado em https://wf5t8vt9cgo9fb-8090.proxy.runpod.net/"
