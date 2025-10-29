#!/usr/bin/env bash
set -e

echo "🚀 Atualizando pacotes..."
apt update && apt install -y \
  git curl wget ffmpeg python3 python3-pip python3-venv \
  build-essential libsndfile1 libgl1 libglib2.0-0 libsm6 libxrender1 libxext6

echo "🧠 Criando ambiente virtual..."
cd /workspace
python3 -m venv venv
source venv/bin/activate

echo "📦 Instalando dependências Python..."
pip install --upgrade pip setuptools wheel
pip install -r /workspace/pod_ffmpeg/requirements.txt

echo "✅ Setup concluído!"
