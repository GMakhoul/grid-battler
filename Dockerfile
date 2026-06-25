# Servidor do Grid Battler (jogo + relay PvP) para o Fly.io.
# Build deterministico: imagem Python enxuta + aiohttp, rodando relay.py.
FROM python:3.12-slim

WORKDIR /app

# instala deps primeiro (cache de build)
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# copia o resto (index.html, relay.py); o .dockerignore tira o que nao precisa
COPY . ./

# o Fly roteia p/ a porta interna; relay.py le PORT (definido no fly.toml)
EXPOSE 8080
CMD ["python", "relay.py"]
