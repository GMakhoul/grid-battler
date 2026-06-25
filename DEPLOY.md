# Hospedar o Grid Battler de graça (jogo + PvP online)

O `relay.py` serve o jogo **e** faz o relay de PvP na mesma URL. Então um único deploy
num host que rode Python já te dá tudo numa **URL fixa HTTPS** (ex.: `https://grid-battler.onrender.com`),
substituindo o `cloudflared`. O cliente já troca pra `wss://` sozinho em HTTPS — nada a mudar no jogo.

Recomendado: **Render (plano free)**. Grátis, URL fixa, suporta WebSocket.
Ressalva: no free, o servidor dorme após ~15 min parado e o **1º acesso depois disso leva ~50s** pra acordar.

---

## Passo 1 — Pôr o código no GitHub

Você precisa de uma conta no GitHub (grátis). O Render lê o código de lá.

### Opção A — pelo site do GitHub (sem terminal, mais simples)
1. Em https://github.com → **New repository**. Nome: `grid-battler`. Pode ser **Public** ou **Private**.
   Não marque "Add a README". Clique **Create repository**.
2. Na página do repo vazio → link **"uploading an existing file"**.
3. Arraste estes arquivos da pasta do projeto:
   `index.html`, `relay.py`, `requirements.txt`, `render.yaml`, `.gitignore`
   (o `handoff.md` e o `permitir-firewall.bat` são opcionais; o resto não precisa).
4. **Commit changes**.

### Opção B — pelo terminal (git)
Na pasta do projeto:
```bash
git init
git add .
git commit -m "Deploy: Grid Battler (jogo + relay PvP)"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/grid-battler.git
git push -u origin main
```
(crie o repo vazio em github.com/new antes, e troque `SEU_USUARIO`).

---

## Passo 2 — Subir no Render

1. Crie conta grátis em https://render.com (dá pra entrar com o GitHub).
2. **New** (canto superior) → **Blueprint**.
3. Conecte/escolha o repositório `grid-battler`. O Render acha o `render.yaml` e mostra o serviço `grid-battler` (plano **Free**).
4. **Apply** / **Create**. Ele instala o `aiohttp` e roda `python relay.py`.
5. Em ~1–2 min aparece a URL pública: `https://grid-battler.onrender.com` (o nome pode variar).

> Se preferir não usar Blueprint: **New → Web Service** → escolha o repo → Runtime **Python 3**,
> Build `pip install -r requirements.txt`, Start `python relay.py`, plano **Free**. Dá no mesmo.

---

## Passo 3 — Jogar

- Abra a URL do Render no navegador → o jogo carrega.
- Para PvP: cada amigo abre a **mesma URL**, toca em **PvP**, um **cria a sala** e o outro **entra com o código**.
- O HTTPS é automático, então o WebSocket vai por `wss://` sem você fazer nada.

---

## Atualizar o jogo depois

- **Opção A (site):** suba o `index.html` novo pelo GitHub (botão de editar/upload). O Render re-deploya sozinho.
- **Opção B (git):** `git add . && git commit -m "ajustes" && git push`. Deploy automático.

---

## Perguntas comuns

- **Custa algo?** Não. O plano Free do Render não pede cartão para web services.
- **Aquele "1º acesso de 50s" incomoda?** Só acontece após 15 min sem ninguém online. Para tirar o sleep,
  o plano pago do Render é ~US$7/mês (Starter). Dá pra mudar depois com 1 clique.
- **Quero domínio próprio** (ex.: `gridbattler.com.br`)? Dá pra apontar um domínio no Render (settings → Custom Domain). O domínio em si é pago no registrador; o Render não cobra a mais.
- **Deploy falhou no build?** Quase sempre é versão de Python/aiohttp. Abra os logs no Render; se for o caso,
  me chame que eu fixo a versão (`requirements.txt` / `PYTHON_VERSION`).

---

## Fly.io — servidor em São Paulo (MELHOR ping no Brasil)

O Render não tem datacenter na América do Sul, então o ping fica ruim no Brasil (~440ms). O **Fly.io tem a região
`gru` (São Paulo)** — hospedar o relay lá derruba o ping pra ~80-160ms. O repo já vem pronto:

- `Dockerfile` — build determinístico (Python + aiohttp + `python relay.py`).
- `fly.toml` — `app = "grid-battler"`, `primary_region = "gru"`, porta interna 8080 (o `relay.py` lê `PORT`).
- `.dockerignore` — deixa a imagem enxuta.

Passos:
1. Conta no https://fly.io (pede cartão mesmo no nível grátis; uma máquina `shared-cpu-1x` que dorme é centavos).
2. Conecte o repositório `GMakhoul/grid-battler` (você já fez). A cada `git push`, o Fly re-deploya.
3. Se um deploy falhar no **"Build image"** (ex.: `unauthorized` / "Dockerfile failed to build"), normalmente era a
   falta do `Dockerfile` — agora que ele existe, é só **re-rodar o deploy** (Deploy → Retry, ou um novo `git push`).
4. URL final: `https://grid-battler.fly.dev` — compartilhe essa (em vez da do Render) para o ping de São Paulo.

> O jogo é o mesmo arquivo; o cliente monta `wss://<host>/ws` sozinho, então tudo (jogo + salas + relay) roda na URL do Fly.
> Dá pra manter o Render também (cada plataforma lê seu próprio config); ou desligar o serviço do Render se migrar de vez.

### ⚠️ IMPORTANTE: o relay precisa de UMA máquina só (estado em memória)

O `relay.py` guarda as salas e a partida **na memória**. Se o Fly rodar **2+ máquinas**, os jogadores
podem cair em máquinas diferentes → a sala existe numa, o amigo entra na outra (vazia) → **a partida não
começa**; e se uma máquina dormir, o **visitante congela** no meio (o host continua jogando local). Por isso o
`fly.toml` usa `auto_stop_machines = "off"` + `min_machines_running = 1`, MAS você também precisa garantir **1 máquina**:

- **Pelo terminal (flyctl):** `fly scale count 1 -a grid-battler`
- **Pelo painel:** menu **Machines** → se houver 2, **apague uma** (deixe a que está em `gru`/São Paulo, estado *started*).

Depois confirme em **Machines**: deve haver **1 máquina**, região **São Paulo (gru)**, *started*. Isso resolve tanto o
pareamento intermitente quanto o loop de rodadas do visitante.

---

## Alternativa: jogo instantâneo, sem PvP online (host estático)

Se um dia você quiser que a **página carregue instantânea** (sem o "acordar" do servidor) e abrir mão do
PvP online (mantendo vs bot e PvP na mesma Wi-Fi), dá pra jogar **só o `index.html`** em GitHub Pages /
Netlify (grátis, nunca dorme). Aí o PvP online ficaria num servidor à parte. É mais setup — peça se quiser
que eu monte esse caminho.
