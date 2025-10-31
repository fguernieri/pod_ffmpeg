🎬 pod_ffmpeg API

Serviço HTTP baseado em FastAPI para:

🧠 Transcrição de áudio/vídeo (OpenAI Whisper)

🎞 Conversão e renderização de mídia (FFmpeg + GPU NVENC)

🎥 Geração de vídeos com efeito Ken Burns (zoom/pan 2D suave ou 3D com profundidade)

⚙️ Estrutura principal
/workspace/
├── pod_ffmpeg/
│   ├── app.py → API principal (FastAPI)
│   ├── setup.sh → Instala dependências
│   ├── boot_env.sh → Inicia o servidor
│   ├── requirements.txt → Pacotes necessários
│   └── ...
├── uploads/ → Onde os arquivos são enviados
│   └── imagens/ → Pasta de imagens para /ffmpeg_ken
├── kenburns_2d/ → Script independente para zoom/pan suave
│   └── kenburns_2d_smooth.py → Efeito Ken Burns 2D (warpAffine + easing)
└── output/ → Onde os vídeos e áudios gerados são salvos

🔧 Instalação
1️⃣ Acesse o diretório do projeto
cd /workspace/pod_ffmpeg

2️⃣ Instale as dependências
bash setup.sh

3️⃣ Inicie o servidor
bash boot_env.sh


O servidor iniciará em:

http://<IP_DO_POD>:8090

🧠 Endpoints disponíveis
/whisper → Transcrição automática (áudio/vídeo → texto)

Descrição:
Transcreve arquivos de áudio/vídeo usando o modelo Whisper da OpenAI.

Exemplo:

curl -X POST http://<IP_DO_POD>:8090/whisper \
  -F "file=@meu_audio.mp3" \
  -F "model_name=small" \
  -F "output_format=text"

/ffmpeg → Conversão de mídia

Descrição:
Converte arquivos de áudio ou vídeo para outros formatos usando FFmpeg.

Exemplo:

curl -X POST http://<IP_DO_POD>:8090/ffmpeg \
  -F "file=@video.mp4" \
  -F "output_format=wav"

/upload → Upload de arquivos

Descrição:
Envia arquivos para o servidor e salva em /workspace/uploads/.

Exemplo:

curl -X POST http://<IP_DO_POD>:8090/upload \
  -F "file=@meu_audio.mp3"


Retorno:

{
  "status": "success",
  "filename": "meu_audio.mp3",
  "saved_as": "uuid_meu_audio.mp3",
  "path": "/workspace/uploads/uuid_meu_audio.mp3"
}

/ffmpeg_ken → 🎞 Efeito Ken Burns automático (GPU NVENC)

Descrição:
Gera automaticamente um vídeo com efeito de zoom/pan (Ken Burns) sobre uma sequência de imagens, sincronizado com o áudio e renderizado com GPU NVENC.

Pré-requisitos:

/workspace/uploads/audio.mp3
/workspace/uploads/imagens/*.png


Exemplo:

curl -X POST http://<IP_DO_POD>:8090/ffmpeg_ken \
  -F "audio_file=meu_audio.mp3" \
  -F "image_pattern=*.png" \
  -F "output_name=meu_video.mp4"


Retorno:

{
  "message": "✅ Vídeo gerado com sucesso (Ken Burns real)!",
  "imagens": 8,
  "tempo_por_imagem": 4.2,
  "duracao_audio": 33.5,
  "output": "/workspace/output/meu_video.mp4"
}


💡 Suporta zoom/pan aleatório, fade-in/out e aceleração total via RTX A4500 (NVENC).

🎥 Efeito Ken Burns 2D (modo independente)

Além da rota /ffmpeg_ken, o projeto inclui o script kenburns_2d_smooth.py — ideal para gerar vídeos curtos a partir de fotos estáticas com movimento suave.

🔧 Exemplo de uso:
cd /workspace/kenburns_2d

python kenburns_2d_smooth.py \
  --image /workspace/uploads/imagens/VID035_imagem_1.png \
  --out outputs \
  --zoom 1.08 \
  --shiftx 0.02 \
  --shifty -0.01 \
  --frames 150 \
  --fps 30


Saída:

/workspace/kenburns_2d/outputs/video_out_smooth.mp4


Características:

🚀 Aceleração por GPU (NVENC)

🌀 Movimento contínuo com warpAffine (sem tremores)

🎚 Easing real (ease_in_out_sine) para suavidade cinematográfica

🖼 Ideal para vídeos narrados ou canais “faceless”

🧩 Fluxo completo de uso

1️⃣ Instala tudo (apenas uma vez)

bash /workspace/pod_ffmpeg/setup.sh


2️⃣ Inicia o servidor

bash /workspace/pod_ffmpeg/boot_env.sh


3️⃣ Testa no navegador ou curl

curl http://<IP_DO_POD>:8090/


4️⃣ Executa o pipeline completo
(upload → transcrição → vídeo):

/upload       → envia áudio e imagens  
/whisper      → gera texto  
/ffmpeg_ken   → cria vídeo final sincronizado  

⚡ Recursos técnicos
Recurso	Descrição
🎬 FFmpeg	Conversão e renderização acelerada por GPU (NVENC)
🧠 Whisper	Transcrição de áudio/vídeo com modelos OpenAI
🎞 Ken Burns 2D/3D	Efeito de zoom/pan com easing e suporte a paralaxe (MiDaS opcional)
🚀 FastAPI	Interface HTTP assíncrona e leve
🧰 CUDA + RTX A4500	Encode e processamento acelerados
🧠 Healthcheck

Verifica se o serviço está online:

curl http://<IP_DO_POD>:8090/


Retorno:

{
  "status": "ok",
  "message": "API FFmpeg + Whisper + Ken Burns ativa 🚀",
  "routes": ["/upload", "/ffmpeg", "/whisper", "/ffmpeg_ken"]
}
