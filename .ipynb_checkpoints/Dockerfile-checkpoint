FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /workspace/pod_ffmpeg

# Instala pacotes básicos
RUN apt update && apt install -y \
    python3 python3-pip python3-venv ffmpeg git curl wget build-essential libsndfile1 && \
    rm -rf /var/lib/apt/lists/*

# Copia o código do projeto
COPY . .

# Cria venv e instala dependências
RUN python3 -m venv /workspace/venv && \
    /workspace/venv/bin/pip install --upgrade pip && \
    /workspace/venv/bin/pip install -r requirements.txt

# Define variável pra cache de modelos
ENV XDG_CACHE_HOME=/workspace/models

# Expõe porta
EXPOSE 8090

# Comando de inicialização
CMD ["/workspace/venv/bin/uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8090"]
