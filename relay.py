#!/usr/bin/env python3
"""
Servidor PvP do Grid Battler (com salas por código).

- Serve o jogo (index.html) em /
- Repassa mensagens entre os 2 jogadores da MESMA SALA via WebSocket em /ws?room=CODIGO
- 1o a entrar na sala = host (roda a simulação); 2o = guest. O relay só encaminha.

Jogar na MESMA Wi-Fi:
  1. No PC:  python relay.py        (rode permitir-firewall.bat uma vez antes)
  2. Abra a URL LAN nos dois aparelhos, toque em "PvP", criem/entrem na mesma sala.

Jogar pela INTERNET (com amigos longe) — túnel Cloudflare:
  1. No PC:  python relay.py
  2. Em outra janela: cloudflared tunnel --url http://localhost:8765
  3. Ele imprime uma URL https://...trycloudflare.com — mande pros amigos.
  4. Cada um abre essa URL, toca "PvP", e um cria a sala e o outro entra com o código.
  (O jogo troca pra wss:// sozinho quando a URL é https.)

Requer: aiohttp (já instalado neste ambiente).
"""
import os
import socket
import pathlib
from aiohttp import web, WSMsgType

ROOT = pathlib.Path(__file__).parent
# Hosts gratuitos (Render, Koyeb, etc.) injetam a porta na variavel de ambiente PORT.
# Localmente, cai no 8765 de sempre.
PORT = int(os.environ.get("PORT", 8765))
rooms = {}  # codigo -> lista de websockets (no maximo 2)


def lan_ip() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        return "127.0.0.1"
    finally:
        s.close()


async def index(request):
    # no-cache = o navegador SEMPRE revalida o index.html com o servidor (via ETag/Last-Modified).
    # Assim cada deploy novo aparece na hora, em vez de servir uma versao velha do cache do navegador.
    # (Continua eficiente: se nada mudou, o servidor responde 304 e nao reenvia o arquivo.)
    return web.FileResponse(ROOT / "index.html", headers={"Cache-Control": "no-cache"})


async def notify_peers(room, exclude=None):
    for p in list(room):
        if p is not exclude and not p.closed:
            try:
                await p.send_json({"t": "peer", "peers": len(room)})
            except Exception:
                pass


async def ws_handler(request):
    ws = web.WebSocketResponse(heartbeat=20)
    await ws.prepare(request)

    code = (request.query.get("room") or "default").upper()[:8]
    room = rooms.setdefault(code, [])

    if len(room) >= 2:                       # sala cheia
        await ws.send_json({"t": "full"})
        await ws.close()
        return ws

    role = "host" if len(room) == 0 else "guest"
    room.append(ws)
    await ws.send_json({"t": "role", "role": role, "room": code, "peers": len(room)})
    await notify_peers(room, exclude=ws)
    print(f"[relay] sala {code}: {role} entrou ({len(room)}/2)")

    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                for p in room:                # encaminha pro outro da mesma sala
                    if p is not ws and not p.closed:
                        await p.send_str(msg.data)
            elif msg.type == WSMsgType.ERROR:
                break
    finally:
        if ws in room:
            room.remove(ws)
        if not room:
            rooms.pop(code, None)
        await notify_peers(room)
        print(f"[relay] sala {code}: alguem saiu ({len(room)}/2)")
    return ws


def main():
    app = web.Application()
    app.add_routes([web.get("/", index), web.get("/ws", ws_handler)])
    ip = lan_ip()
    print("=" * 56)
    print("  Grid Battler — servidor PvP")
    print(f"  Mesma Wi-Fi:  http://{ip}:{PORT}")
    print(f"  Internet:     rode  cloudflared tunnel --url http://localhost:{PORT}")
    print("=" * 56)
    web.run_app(app, host="0.0.0.0", port=PORT, print=None)


if __name__ == "__main__":
    main()
