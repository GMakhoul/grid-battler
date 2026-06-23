# Project Grid — Handoff

Single-file, mobile-first **grid battler** (Mega Man Battle Network × One Step From Eden, Supercell-style progression). Core hook: **Program Advance** — fuse two identical/related cards into a stronger one and fire it reactively. **North star of game feel: the "ecstasy" payoff of the big fused hit.** That climactic moment is the whole point — every change is judged against it.

---

## Run it

- **Play / dev:** `python -m http.server 5173` in the project root → open `index.html`. (Preview MCP server is named `grid`, see `.claude/launch.json`.) The game is **fully self-contained** — no external deps, runs offline from `file://`.
- **Online PvP (2 devices):** `python relay.py` (aiohttp WS relay, port 8765, rooms by `?room=CODE`). Title → "PvP online (com amigo)" → criar/entrar sala. First peer = host (runs the sim, host-authoritative), second = guest.
  - Local Wi-Fi: run `permitir-firewall.bat` once (opens port 8765), open `http://<PC-IP>:8765` on both phones.
  - Over the internet (quick/dev): Cloudflare quick tunnel — `cloudflared tunnel --url http://localhost:8765` (URL rotates each restart, PC must stay on; cloudflared not installed → `winget install Cloudflare.cloudflared`).
  - **Permanent free hosting (2026-06-23, the recommended path now):** **Render free web service** — one deploy of `relay.py` serves the game *and* the relay on a stable `https://*.onrender.com`, so the client's `wss://<same host>/ws` (index.html:843, already protocol-aware) just works with **zero client changes**. Repo is deploy-ready: `relay.py` reads `PORT` from env, plus `requirements.txt` (`aiohttp>=3.10,<4`), `render.yaml` (Blueprint: free plan, `python relay.py`), `.gitignore`. Steps in `DEPLOY.md`. Caveat: free instance sleeps after ~15 min idle (~50s cold start). Verified locally: `PORT=8799 python relay.py` serves `/` 200 + `<title>Grid Battler</title>`. **User must do the GitHub push + Render account themselves** (can't create accounts for them).

## Files

| File | Role |
|---|---|
| `index.html` | **The entire game** — all logic, UI, canvas render. The only file you normally edit. ~1000+ lines. |
| `relay.py` | aiohttp WebSocket relay for online PvP (rooms, host/guest pairing). Reads `PORT` from env (cloud) / 8765 local. Stable; rarely touched. |
| `permitir-firewall.bat` | Self-elevating Windows firewall rule for port 8765. |
| `requirements.txt` / `render.yaml` / `DEPLOY.md` | Deploy bundle for **Render free** (see Run/host section). `.gitignore` excludes `.claude/` + `__pycache__/`. |
| `.claude/launch.json` | Preview config (server `grid`, port 5173). |

Memory: `~/.claude/.../memory/game-concept-grid-battler.md` — the **authoritative design log** (locked decisions, every balance pass, why past attempts failed). Read it before big changes; update it after.

---

## Architecture essentials (read before editing `index.html`)

- **Everything lives in one closure IIFE** `(() => { "use strict"; ... })()`. Globals like `S`, `CHIPS`, `spawnProj` are **NOT reachable from `preview_eval`** — this shapes how you test (see below).
- **Symmetric two-side engine.** Sides `S.A` (bottom, `dir -1`) and `S.B` (top, `dir +1`), each with full state. Controllers per side: `local` / `bot` / `local2` / `remote`. Single-player = A local vs B bot.
- **Direction-aware geometry — never hardcode "up".** Use `fwd(s,n)`, `foeBackRow(s)`, `foeRows(s)`. Per-tile ownership is `S.owner[r][c]` = `'A'`/`'B'` (area-grab steals tiles with a `GRAB_DUR=5s` timer shown as tile color).
- **Effect engine kinds:** `strike / proj / wave / beam / mine / boomerang / tornado / spawner / yoyo / cone / aura`. Primitives: `spawnProj`, `strike`, `rectAhead`, `spawnYoyo`, `spawnCone`, `spawnAura`, `moveDash`, `pushFoe`, `addBleed`, `healSide`. Reuse these for new cards.
- **Channel/root mechanic (gun del sol):** `spawnCone` roots the caster (`s.rooted` gates `moveSide`) and optionally shields it (`s.chanMit` halves dmg in `damageSide`) while a fixed cone ticks. Both side fields are init'd, reset in `resetSide`, decayed in `updateSide`; `rooted` is in `sideSnap`, cone's `dur`/`finale` in `effSnap`.
- **Aura mechanic (radiação — opposite of root):** `spawnAura(s,{radius,dmg,every,dur,color})` pushes a `kind:"aura"` effect that **follows the caster every frame** (`e.col/e.row = e.atk.col/row`, `e.tiles = auraTiles(col,row,radius)`), pulsing `dmg` to the foe whenever it sits on a neighbor tile (Chebyshev ≤ radius, center excluded). Caster stays mobile → rewards crowding the enemy / advancing onto stolen ground. `tiles` are recomputed on the host each frame so `effSnap` (which already serializes `tiles`/`col`/`row`/`color`/`t`/`dur`) keeps the guest's draw correct. Draw = toxic tile fog + spinning radiation trefoil (`drawRadCore`).
- **Per-card visuals — two cosmetic hooks (every card now has a unique identity; zero gameplay/hit-logic change):**
  - **`vfx` on `strike`:** `strike(s,tiles,delay,telegraphed,color,vfx)` stores `vfx`+origin(`oc`/`orow`); `drawStrikeVfx(e)` switches: `"lob"` (granada/crossbomb/meteor — parabola from caster to target + growing shadow), `"slash"` (espada/wideblade/dreamsword/rushblade — arc sweep pivoting on caster), `"spear"` (lança/trident — triangular marker over **each** tile + dashed thrust line), `"slam"` (martelo/quaker — hammer drops on center + shockwave rings), `"tornado"` (tornado — spinning swirl).
  - **`style` on `spawnProj`:** `drawProj(e)` switches: `"bolt"` (canhão — elongated bullet+trail), `"charge"` (mega/zeta canhão — pulsing charged orb+halo), `"wave"` (onda/tsunami — **curved wave crest, not a ball**), `"blunt"` (recuo — ram ring+push arrow), `"spark"` (metralha/gatling — small spark+trail).
  - Other kinds keep their own identity (boomerang spin, mine pulse, beam column, **yoyo now has a visible string** to its launch point via `oc`/`orow`, guard/reflector rings, gun del sol cone, area-grab tile-flip).
  - All snapped via `vfx`/`style`/`tint`/`dir`/`oc`/`orow` in `effSnap` so PvP guests match. **Extend by adding a case + passing the tag in the chip's `cast`.** Verified by intercepting canvas ops (ellipse/distinct strokeStyles) while firing — bolt/wave/blunt/slam/tornado/spear/yoyo-string all drew; zero console errors.
- **Energy + fusion economy:** one regenerating energy bar gates casts. Spend **10 energy → 1 fusion point** (max 3); each fuse costs 1 point. Fusion gesture = **drag one card onto a recipe-compatible card** (craft-then-fire, stays in hand). PA chips (`pa:true`) trigger the freeze + shake + rising sound + small rising name label.
- **Netcode = host-authoritative**, 30Hz snapshots. `makeSnap`/`applySnap`, `sideSnap` (incl. hand), `effSnap` (draw-only, strips circular `atk`/`foe` refs). Guest renders snapshots only (no sim) and sends `{t:'in',...}` inputs. **Any new per-side or per-effect field that the guest must see has to be added to the snapshot functions** (e.g. `effSnap` carries `rows` for yoyo). Input always routed through `cmdMove/cmdFire/cmdFuse`.
- **Perspective flip:** guest renders itself at the bottom via `S.flip` (180° canvas rotate); floaters/text drawn in a separate un-rotated, flip-aware pass so numbers stay upright. Guest movement input is inverted in `cmdMove`.

### Layout / CSS gotchas (cost real time before)
- `.screen` is `position: absolute; inset: 0; display:flex; flex-direction:column`. **NEVER set `position` on any `#screen-*`** — it overrides `.screen` and collapses the battle layout (arena shrinks at top, hand unpins). Overlays like `#roundBanner` use `position:absolute` and center fine *because* `.screen` is the absolute containing block.
- **iOS Safari ignores `user-scalable=no`.** Zoom is blocked in JS instead: `preventDefault` on `gesturestart/change/end`, on multi-touch **`touchstart`+`touchmove`** (blocks pinch already at finger-down), and a `<300ms` double-tap `touchend` blocker. Single taps/swipe stay free (gameplay uses pointer events). Don't remove these.
- **Android edge-swipe "back" guard:** the movement swipe sometimes triggered the browser's back navigation. Trapped via `history.pushState` on load + re-push on `popstate` (single-page game, so back has no real destination). Combined with `overscroll-behavior:none` on the root. **Device-level gestures (pinch/edge-back) are NOT verifiable in the headless preview — only real iPhone/Android confirm the feel.**
- Mobile movement = **swipe on `#arenaWrap`** (`touch-action:none`); `#hand` is full-width. Desktop: P1 WASD+1-5, P2 arrows+6-0.

### Navigation / flow model (design rule: separate *prepare* from *play*)
- **Title = hub.** Shows TWO independent loadout cards (`#charCard` → personagem, `#deckCard` → baralho; populated by `buildTitleScreen()`), then play modes under "jogar": `vs bot` (primary) / PvP / 2-player.
- **Char + Deck = pure editor, fully INDEPENDENT (they don't chain).** Char footer is `#charDone` "concluir ✓" → `show(loadoutReturn)` (back to hub, NOT to deck). Deck footer `#fightBtn` "concluir ✓" and `#deckBack` → `show(loadoutReturn)`. They NEVER start a battle.
- **`loadoutReturn`** = where the editor was opened from: `"title"` (a hub card) or `"result"` (`#resDeckBtn`). **Starting a match happens only from the hub buttons + result `#againBtn` (still routes `readyRematch` for net).**
- **Deck must be EXACTLY 8 to play** (`deckReady()`; mono-/half-decks were a consistency exploit, and Clash uses fixed 8). Every match entry is wrapped in `gate(fn, from)`: if `!deckReady()` it routes to the deck screen to finish instead of starting. `buildTitleScreen` dims the play buttons (`.locked`), shows `#deckHint` ("complete o baralho (N/8)…"), and flags `#deckCard.warn` when incomplete. Load-sanitize still only pads when `<4`; `DEFAULT_DECK` is 8 so fresh saves are ready.
- **Deck builder is tap-to-add (reverted from the sheet-stepper — user preferred quick clicking):** tap a pool card = add a copy (respects max-4/deck-8); tap a deck-tray slot = remove; a small **ⓘ** on each card opens an **info-only** `#chipSheet` (description + the fusions it enables; no +/- stepper). `updateDeckCnt` shows `N/8 · completo✓|faltam N · custo médio`.

---

## Current balance (the tuning knobs)

**Round structure:** best-of-3. Consts at top of IIFE: `ROUND_TIME=90, WINS_NEEDED=2, INTER_ROUND=2.4`. On timeout, higher HP wins (A wins exact ties). `endRound`→`endMatch`/`resetRound` handle the flow; HUD `#roundHud` (Round · m:ss · score, timer coral ≤10s) + `#roundBanner` between rounds.

**The balance model (key insight): DPS is energy-gated, not tap-gated.**
`effective DPS = (1/regen) × (dmg per energy) × dmgMult × accuracy`; `round length ≈ HP ÷ winner-DPS`. Empirically realistic winner DPS ≈ 10–14; perfect-aim ceiling ≈ 40–56.

**HP is the round-length dial** (scale it; keep card damage punchy). Current `CHARACTERS` (HP was doubled to land ~90s rounds):

| Char | HP | moveDelay | dmgMult | regen | notes |
|---|---|---|---|---|---|
| Vanguarda ♜ | 1040 | .21 | 1.15 | .9 | tank melee |
| Lâmina ♞ | 640 | .10 | 1.0 | .82 | fast/fragile |
| Artilheiro ♝ (default) | 800 | .17 | 1.0 | .62 | ranged, fast energy |
| Tático ♛ | 800 | .16 | 1.0 | .74 | drawSpeed .6, maxEnergy 12 |

Bonus point = **+88 HP** (3 free points into hp/mov/dmg at char screen). Bot/guest-default B HP = 800. **If playtests feel too timer-heavy → lower HP ~10–20%; too short → raise it.** No elemental damage (locked design rule). No undodgeable attacks (locked design rule).

### Card roster (recent state)
- **Cannon line (non-piercing — walking back never double-hits):** canhão (2e, 60) → megacannon (5e, 230) → **zetacannon** (8e, 160, `boom`): single projectile that ONLY explodes the backline *if the shot reaches it* (3-wide, 120; back-center = 2×). Dodgeable by not camping the back row.
- **Onda line (PIERCING — its identity is punishing retreat):** onda (3e, 80) → tsunami (6e, 95 + push). Retreating into it = 2nd instance. **Recipe = recuo + onda** (`["push","wave","tsunami"]`, changed 2026-06-23 from onda+onda — "recuo + onda = a wave that shoves you back" reads better; freed up onda+onda).
- **Sword (short-range, x×y = cols×rows):** espada T1 = 1×1 (120). wideblade T2 = stab 1×2 (95) + sweep 3×1 (85). dreamsword T3 = focused 1×2 (120) + wide 3×2 (`rectAhead`, 85, easier to hit).
- **Yoyo line (column out-and-back, hits on path both ways = 2×):** yoyo (3e, 55) → yoyospin (5e, 65, spins 2× at return tile) → **yoyorend** (8e, 38 + **bleed** 24/hit). `spawnYoyo(s,dmg,{reach,apexHits,bleed})`.
- **Gun del Sol line (MMBN6 — channeled CONE that ROOTS the caster; dodge by leaving the cone):** gundelsol T1 (4e, 3s, focus 15 / spread 10) → **sol abrasador** T2 (gun+gun, 6e, 1.5s burst, 40/26) → **erupção solar** T3 (gun+**guarda**, 8e, 2s, wide 3×2, ½-dmg shield while channeling + **supernova** finale +100). `spawnCone(s,{focus,spread,dur,every,wide,mit,finale,color})`.
- **Radiação line (mobile DoT aura — rewards crowding/area-stealing, the anti-gun-del-sol):** radiação T1 (**4e**, raio 1 = 8 vizinhos, 12/0.5s for 5s, **you can move**) → **colapso** (rad+rad, 7e, **raio 2** giant field, 22/0.45s, 3.6s — near-inescapable up close, still dodgeable at Chebyshev ≥3) → **precipitação** (rad+**roubo de área**, 6e, steals front row **and** lays a long 5s aura, 14/0.5s — seize+contaminate terrain). `spawnAura`.
- **Area control:** roubo de área (**4e**, was 3e — bumped 2026-06-23 to tax the territory steal) → invasão (rad/areagrab fusions above; areagrab+areagrab → invasão, 2 rows).
- **Utility:** recuo (2e, 30, `pushBack` → slams foe to backline), investida (**1e, pure movement** `moveDash(s,2)`), reparo/heal (4e, 170), guarda, plus laser/martelo/mina/tornado/granada/bumerangue/lança/metralha.
- **Bleed DoT:** `addBleed` → ticks 12 dmg / .35s until drained; kill-credit via `bleedBy`. Only yoyorend applies it.
- **Deck builder:** pool cards show cost badge + `×N` copies + "⚛ funde" tag (dim when maxed). **Tap = add** a copy; deck-slot tap = remove; **ⓘ** opens an info-only `#chipSheet` (`openChipSheet`: desc + fusions, no stepper). Footer shows avg cost + `N/8` completeness. (See the flow section for the exactly-8 play gate.)
- **Removed (don't re-add without reason):** dispersão, estrela (homing too strong), alabarda, morteiro (AoE only matters >2 players), lâmina explosiva, raio de choque (all redundant). Saved decks are sanitized on load.

---

## Testing in this environment (important quirks)

- The preview/headless tab is usually `document.hidden=true` → **`requestAnimationFrame` is paused (blank canvas) and the screenshot tool HANGS (~30s timeout).** This is an env artifact, NOT a game bug — real phones/visible tabs run fine.
- **Workaround:** in `preview_eval`, override `window.requestAnimationFrame = cb => setTimeout(()=>cb(performance.now()),16)` to force the loop, then verify via **DOM reads, canvas `getImageData` pixel sampling, intercepting `CanvasRenderingContext2D.prototype.fillText`, and damage-geometry inference** (since `S` is unreachable from outside the closure).
- **2-step fusions can't be runtime-fired vs a passive dummy** (building 2 fusion points needs enough casts to kill it; an active bot kills the tester). Verify those via the shared primitives + a 1-step fusion instead, and say so honestly.
- Long async loops in an eval exceed the 30s tool limit → use a background-runner pattern (write progress to `window.__test`, poll with short evals).
- **Two real phones can't be tested from here** — final 2-device feel is the user's call. Engine + relay forwarding ARE verifiable here.

---

## Open / pending

- **No active task.** User confirmed card balance "parece bem bom"; layout fixed & verified.
- **iOS zoom reforçado + trava de "voltar" no Android** (2026-06-21): bloqueio de pinça agora pega `touchstart` multitoque, e o gesto de borda do Android é preso via `history`/`popstate`. **Aguardando reteste em iPhone/Android reais** — não verificável no headless. Se ainda houver zoom no iPhone, o caminho definitivo é PWA (Adicionar à Tela de Início + `apple-mobile-web-app-capable`), que roda fullscreen sem os gestos do Safari.
- **UX/cards pass (2026-06-21):** split loadout into 2 hub cards; char/deck = pure editor (no battle launch); Clash-style deck page (cost badges, copies, tap→detail-sheet with fusions, avg cost); **new Gun del Sol cone line** (gundelsol/sol abrasador/erupção solar — channeled cone that roots the caster). Verified: cone DoT+root, deck sheet/stepper, flow. **Needs real-playtest calibration** of the cone numbers + the root commitment feel.
- **Radiation + tsunami-recipe + area-cost pass (2026-06-23):** (1) **Tsunami recipe → recuo + onda** (was onda+onda). (2) **New radiação card** + `aura` effect kind (mobile DoT that follows the caster; fusions colapso [rad+rad, raio 2] and precipitação [rad+roubo de área, steal+contaminate]). (3) **roubo de área 3e → 4e** to tax area-stealing. Verified in a live battle (rAF-override): radiação ticks 12 to an adjacent foe, follows on the move, no self-damage, 0 console errors; colapso fusion casts clean; deck-pool/recipe/cost all correct in the UI. **Needs real-playtest calibration** of radiação's dmg/cost vs the area-steal playstyle (esp. how oppressive colapso's raio-2 feels, and whether 4e roubo de área is enough).
- Calibrate the reworked fusions (zetacannon / dreamsword / yoyospin / yoyorend / bleed / **gun del sol line**) from real PvP feel — only runtime-unverified items.
- Tune HP if rounds hit the 1:30 cap too often (the `CHARACTERS` dial).
- **Hosting (2026-06-23):** deploy bundle for **Render free** is ready (`requirements.txt`/`render.yaml`/`DEPLOY.md`; `relay.py` reads `PORT`). **Next action is the user's:** push to GitHub + create the Render Blueprint (see `DEPLOY.md`). This replaces the rotating cloudflared URL with a stable free `*.onrender.com`. cloudflared remains the quick local-tunnel fallback.
- Bot AI is still aggressive/unbalanced — tune later.
- Progression / customization depth deferred until the core loop is proven fun.

## Working with the user (Gabriel)

- Speaks **Portuguese**; reply in Portuguese. Game text/UI is Portuguese.
- He has the latest Godot for the real build — this `index.html` is the **feel-validation prototype**.
- Be honest about what was/wasn't runtime-verified vs inferred. After meaningful changes, update the design-log memory.
