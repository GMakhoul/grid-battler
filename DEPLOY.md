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

## Alternativa: jogo instantâneo, sem PvP online (host estático)

Se um dia você quiser que a **página carregue instantânea** (sem o "acordar" do servidor) e abrir mão do
PvP online (mantendo vs bot e PvP na mesma Wi-Fi), dá pra jogar **só o `index.html`** em GitHub Pages /
Netlify (grátis, nunca dorme). Aí o PvP online ficaria num servidor à parte. É mais setup — peça se quiser
que eu monte esse caminho.
