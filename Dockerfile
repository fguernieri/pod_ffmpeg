# ======================================================
# 🎬 pod_ffmpeg - API com FFmpeg + Whisper + Ken Burns
# Base: Ubuntu 22.04 + CUDA 12.4 (Runtime NVENC Ready)
# ======================================================
FROM nvidia/cuda:12.4.0-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /workspace/pod_ffmpeg

# ======================================================
# 🧩 Dependências do sistema
# ======================================================
RUN apt update && apt install -y \
    python3 python3-pip ffmpeg git curl wget build-essential \
    libsndfile1 libgl1-mesa-glx libglib2.0-0 && \
    rm -rf /var/lib/apt/lists/*

# ======================================================
# 📦 Copia os arquivos do projeto
# ======================================================
COPY . .

# ======================================================
# ⚙️ Instala dependências Python
# ======================================================
RUN pip install --upgrade pip
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
RUN pip install --no-cache-dir -r requirements.txt

# ======================================================
# 🧠 Cache persistente para modelos (Whisper, Torch)
# ======================================================
ENV XDG_CACHE_HOME=/workspace/models
ENV TRANSFORMERS_CACHE=/workspace/models
ENV HF_HOME=/workspace/models

# ======================================================
# 🌐 Expõe porta da API
# ======================================================
EXPOSE 8090

# ======================================================
# 🚀 Inicializa FastAPI
# ======================================================
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8090"]
