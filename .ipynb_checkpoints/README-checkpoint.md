# 🎬 pod_ffmpeg API

Serviço HTTP baseado em **FastAPI** para:
- 🧠 **Transcrição de áudio/vídeo (OpenAI Whisper)**
- 🎞 **Conversão e renderização de mídia (FFmpeg + GPU NVENC)**
- 🎥 **Geração de vídeos com efeito Ken Burns (zoom/pan automático via MoviePy)**

---

## ⚙️ Estrutura principal

/workspace/
├── pod_ffmpeg/
│ ├── app.py → API principal (FastAPI)
│ ├── setup.sh → Instala dependências
│ ├── boot_env.sh → Inicia o servidor
│ ├── requirements.txt → Pacotes necessários
│ └── ...
├── uploads/ → Onde os arquivos são enviados
│ └── imagens/ → Pasta de imagens para /ffmpeg_ken
└── output/ → Onde os vídeos e áudios gerados são salvos

yaml
Copiar código

---

## 🔧 Instalação

1️⃣ **Acesse o diretório do projeto**
```bash
cd /workspace/pod_ffmpeg
2️⃣ Instale as dependências

bash
Copiar código
bash setup.sh
3️⃣ Inicie o servidor

bash
Copiar código
bash boot_env.sh
O servidor iniciará em:

cpp
Copiar código
http://<IP_DO_POD>:8090
🧠 Endpoints disponíveis
/whisper → Transcrição automática (áudio/vídeo → texto)
Descrição:
Transcreve arquivos de áudio/vídeo usando o modelo Whisper da OpenAI.

Exemplo:

bash
Copiar código
curl -X POST http://<IP_DO_POD>:8090/whisper \
  -F "file=@meu_audio.mp3" \
  -F "model_name=small" \
  -F "output_format=text"
/ffmpeg → Conversão de mídia
Descrição:
Converte arquivos de áudio ou vídeo para outros formatos usando FFmpeg.

Exemplo:

bash
Copiar código
curl -X POST http://<IP_DO_POD>:8090/ffmpeg \
  -F "file=@video.mp4" \
  -F "output_format=wav"
/upload → Upload de arquivos
Descrição:
Envia arquivos para o servidor e salva em /workspace/uploads/.

Exemplo:

bash
Copiar código
curl -X POST http://<IP_DO_POD>:8090/upload \
  -F "file=@meu_audio.mp3"
Retorno:

json
Copiar código
{
  "status": "success",
  "filename": "meu_audio.mp3",
  "saved_as": "uuid_meu_audio.mp3",
  "path": "/workspace/uploads/uuid_meu_audio.mp3"
}
/ffmpeg_ken → Vídeo com efeito Ken Burns 🎞
Descrição:
Gera automaticamente um vídeo com efeito de zoom/pan (Ken Burns) sobre uma sequência de imagens, sincronizado com o áudio e renderizado com GPU NVENC.

Pré-requisitos:

swift
Copiar código
/workspace/uploads/audio.mp3
/workspace/uploads/imagens/*.png
Exemplo:

bash
Copiar código
curl -X POST http://<IP_DO_POD>:8090/ffmpeg_ken \
  -F "audio_file=meu_audio.mp3" \
  -F "image_pattern=*.png" \
  -F "output_name=meu_video.mp4"
Retorno:

json
Copiar código
{
  "message": "✅ Vídeo gerado com sucesso (Ken Burns real)!",
  "imagens": 8,
  "tempo_por_imagem": 4.2,
  "duracao_audio": 33.5,
  "output": "/workspace/output/meu_video.mp4"
}
💡 Suporta zoom/pan aleatório, fade-in/out e aceleração total via RTX A4500 (NVENC).

🧩 Fluxo completo de uso
1️⃣ Instala tudo (apenas uma vez):

bash
Copiar código
bash /workspace/pod_ffmpeg/setup.sh
2️⃣ Inicia o servidor:

bash
Copiar código
bash /workspace/pod_ffmpeg/boot_env.sh
3️⃣ Testa no navegador ou curl:

bash
Copiar código
curl http://<IP_DO_POD>:8090/
4️⃣ Executa o pipeline completo (upload → transcrição → vídeo):

/upload → envia áudio e imagens

/whisper → gera texto

/ffmpeg_ken → cria vídeo final sincronizado

⚡ Recursos técnicos
Recurso	Descrição
🎬 FFmpeg	Conversão e renderização acelerada por GPU (NVENC)
🧠 Whisper	Transcrição de áudio/vídeo com modelos OpenAI
🎞 MoviePy	Efeito Ken Burns real com zoom/pan dinâmico
🚀 FastAPI	Interface HTTP assíncrona e leve
🧰 CUDA + RTX A4500	Encode e processamento com aceleração NVENC

🧠 Healthcheck
Verifica se o serviço está online:

bash
Copiar código
curl http://<IP_DO_POD>:8090/
Retorno:

json
Copiar código
{
  "status": "ok",
  "message": "API FFmpeg + Whisper + Ken Burns ativa 🚀",
  "routes": ["/upload", "/ffmpeg", "/whisper", "/ffmpeg_ken"]
}