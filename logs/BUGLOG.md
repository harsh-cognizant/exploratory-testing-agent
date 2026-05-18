# BUGLOG — Exploratory Testing & Coverage Gap Discovery Agent
**Project started:** 2026-05-13

Bugs numbered sequentially: BUG-001, BUG-002, ...
Status: OPEN | INVESTIGATING | FIXED | WONTFIX | DEFERRED

---

## BUG-001 — AgentMemory init crashes when sentence-transformers can't reach huggingface.co — Status: FIXED
**Discovered:** 2026-05-18 06:55 by Claude Code during first end-to-end scan against corp network
**Phase / File(s) / Severity:** Phase 5 / `engine/memory.py` / HIGH

### Symptoms
First /scan call against the demo-app produced 5 consecutive SSL errors in the uvicorn log:
```
'[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed: unable to get local issuer certificate (_ssl.c:1028)'
thrown while requesting HEAD https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/resolve/main/./modules.json
Retrying in 1s [Retry 1/5].
```
After the retry storm, `AgentMemory.__init__` raised, the orchestrator caught it, and every subsequent memory call also crashed with `Cannot send a request, as the client has been closed.` because the underlying httpx client had been torn down mid-init.

### Reproduction steps
1. Fresh venv, fresh `~/.cache/huggingface/` (no cached model)
2. Network with TLS proxy that intercepts huggingface.co
3. POST /scan → orchestrator calls `_get_memory()` → `AgentMemory()` → `SentenceTransformer('all-MiniLM-L6-v2')` → cascading SSL failure

### Root cause
`engine/memory.py::AgentMemory.__init__` constructed `SentenceTransformer(...)` without try/except. The constructor probes huggingface.co for the latest model manifest before falling back to cache — on a corp proxy that probe fails, and the failure propagates out.

### Fix applied
- Added `_is_model_cached()` helper. When the model directory exists in the HF cache, `HF_HUB_OFFLINE=1` is pre-set so the probe is skipped entirely.
- Wrapped the `SentenceTransformer(...)` call in `try/except`. On failure, `self.disabled = True` and every public method short-circuits to a no-op (`store_finding`, `query_similar`, `get_memory_adjustment` all return early). Memory layer effectively disables; the scan still completes.
- Added a clear one-line WARNING log explaining the disable and pointing at HF as the cause.

### Fix verified by
Subsequent scans run end-to-end with `AgentMemory disabled — embedding model unavailable (...). Memory-driven risk adjustment will be skipped this run.` logged once at the start. No SSL retry storm. No mid-scan crashes.

**Fixed:** 2026-05-18 07:20  **See also:** CHANGELOG v0.9.1

---

## BUG-002 — Python rejects corp TLS proxy chain (CERTIFICATE_VERIFY_FAILED everywhere) — Status: FIXED
**Discovered:** 2026-05-18 07:30 by Claude Code while testing OpenRouter connectivity
**Phase / File(s) / Severity:** Cross-cutting / `api/main.py`, `requirements.txt` / HIGH

### Symptoms
Every outbound HTTPS request from inside the venv failed with:
```
httpcore.ConnectError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed:
unable to get local issuer certificate (_ssl.c:1028)
```
Affected hosts: `huggingface.co` (BUG-001), `openrouter.ai`, `api.anthropic.com`. Verified the corp CA *is* installed in the Windows certificate store (other Windows-native tools like Edge / Outlook / `curl --ssl-no-revoke` succeed) — Python wasn't using it.

### Reproduction steps
1. Cognizant corp Windows machine (Zscaler client active, corp CA installed via GPO)
2. `python -c "import httpx; httpx.get('https://huggingface.co/')"` → SSL: CERTIFICATE_VERIFY_FAILED
3. Python's `certifi` bundle does not contain the corp CA, so the chain doesn't validate

### Root cause
Python's `ssl` module defaults to `certifi`'s CA bundle. Windows machines store their trust roots in the OS-level certificate store, not in `certifi`. Corp CAs distributed via Group Policy don't reach the bundle.

### Fix applied
- Added `truststore>=0.9.0` to `requirements.txt`.
- `api/main.py` calls `truststore.inject_into_ssl()` *before any HTTPS-using module is imported* (above the `from dotenv import load_dotenv` line and well before `from api.routes import …` which transitively imports anthropic + chromadb + sentence-transformers).
- Wrapped in `try/except ImportError` so non-Windows / non-corp environments are unaffected if `truststore` is missing.

### Fix verified by
Direct test from inside the venv:
```
.\venv\Scripts\python.exe -c "import truststore; truststore.inject_into_ssl(); import httpx; print(httpx.get('https://api.anthropic.com/').status_code)"
→ 404
```
404 from Anthropic is success here — it means the TLS handshake completed and Python got an HTTP response. Before the fix the call never got past the handshake.

**Fixed:** 2026-05-18 07:50  **See also:** CHANGELOG v0.9.1

---

## BUG-003 — `nodes_explored` always 0 when scan finds no bugs — Status: FIXED
**Discovered:** 2026-05-18 09:15 by Claude Code while reviewing the dashboard scan-status feedback
**Phase / File(s) / Severity:** Phase 6 / `agent/brain.py` / MEDIUM

### Symptoms
Even after a clean end-to-end scan that visited every page, the `/scan/{id}/status` response returned `nodes_explored: 0` whenever the scan produced 0 findings. From the dashboard's perspective the scan looked like it had done nothing.

### Reproduction steps
1. Run any scan that completes without finding a bug (easy when the LLM is unreachable and persona action lists are empty / mocked-to-no-bugs)
2. Poll `/scan/<id>/status` → `nodes_explored=0` despite the explorer having actually visited multiple pages

### Root cause
`agent/brain.py` was computing `state["nodes_explored"] = len(set(f.get("node_id") for f in all_findings))`. When `all_findings` was empty, the set was empty, and the counter never advanced.

### Fix applied
- Added an `explored_pages: set[str]` accumulator in the exploration loop.
- Every successful `explore_node` call adds the `node_id` to the set, regardless of whether findings came back.
- `state["nodes_explored"] = len(explored_pages)` after every iteration.

### Fix verified by
Re-ran the scan in offline mode (no real findings). `nodes_explored` advances from 0 → 1 → 2 → 3 → 4 as each page is visited.

**Fixed:** 2026-05-18 09:30  **See also:** CHANGELOG v0.9.1

---

## BUG-004 — `/cart` and `/checkout` forms never render during exploration (CartProvider useEffect race) — Status: FIXED
**Discovered:** 2026-05-18 11:30 by Claude Code after first successful offline scan returned no high-severity findings
**Phase / File(s) / Severity:** Phase 4 / `engine/explorer.py` / HIGH

### Symptoms
Every `fill` action on `/cart` and `/checkout` timed out with `Timeout on action N for <persona> on <path>; continuing`. Findings produced for these pages were limited to incidental console errors (404 on a static asset). The intended demo-app bugs (BUG-003 negative quantity, BUG-004 invalid card, BUG-006 non-numeric quantity) were never triggered because the forms didn't exist in the DOM.

### Reproduction steps
1. Start demo-app fresh (no prior cart in localStorage)
2. Launch a scan with `confused_user` persona via /scan
3. Watch the explorer phase: on `/cart` and `/checkout` the page renders the empty-cart placeholder (no form fields), every `page.fill('[data-testid=quantity-input-1]', ...)` times out after 8 s

### Root cause
`demo-app/pages/_app.jsx` `CartProvider` declares two `useEffect`s in this order:
```jsx
useEffect(() => {                                     // read effect
  const savedCart = localStorage.getItem('cart');
  if (savedCart) setCartItems(JSON.parse(savedCart));
}, []);
useEffect(() => {                                     // write effect
  localStorage.setItem('cart', JSON.stringify(cartItems));
}, [cartItems]);
```
React runs both effects after the first commit. The write effect fires with the *initial* `cartItems = []`, **clearing** any localStorage entry from a previous session **before** the read effect's `setCartItems(savedCart)` has actually committed. Net result: every fresh page mount empties the cart on the way in.

The previous fix attempt (a per-`explore_node` `_seed_cart_state` that opened a separate page in the same context, clicked Add-to-Cart, then closed) didn't survive the subsequent `page.goto(target_url)`: the target page mounted CartProvider fresh and clobbered the seeded localStorage entry.

### Fix applied
Refactored to `_seed_cart_and_navigate()`:
1. `page.goto('/products')` — seed page
2. Click `[data-testid='add-to-cart-btn-1']` — cartItems becomes `[product]`, write effect persists it
3. Click `a[href='/cart']` (or `'/checkout'`) — **Next.js `<Link>` client-side navigation**, CartProvider does *not* remount, so the seeded cart state survives

The explorer skips its own `page.goto(target_url)` when the seed+navigate path succeeded.

### Fix verified by
Re-running the same scan: explorer reaches `/cart` and `/checkout` with the cart populated. `page.fill('[data-testid='fullname-input']', …)` returns in <100 ms instead of timing out.

**Fixed:** 2026-05-18 13:15  **See also:** CHANGELOG v0.9.1, DEVLOG 2026-05-18

---

## BUG-005 — Corp Zscaler blocks `openrouter.ai` and `huggingface.co` at URL filter — Status: OPEN (system-side)
**Discovered:** 2026-05-18 07:55 by Claude Code while testing OpenRouter connectivity end-to-end
**Phase / File(s) / Severity:** Cross-cutting / environment, not code / HIGH (blocks live LLM exercise of the agent)

### Symptoms
After `truststore` fix (BUG-002), the TLS handshake to `openrouter.ai` succeeds, but the response body is HTML:
```html
<h2>Security Exception</h2>
<ul>
<li>If you believe you received this message in error, please click here to raise a security exception request…</li>
<li>Category: Security Exception</li>
<li>Service: CS_Corporate Security</li>
<li>Service Offering: Unblock Specific URLs (Zscaler).</li>
</ul>
```
The Anthropic SDK can't parse HTML as JSON and reports `Connection error`. Every persona-page combo records as "API failed".

The same block page is returned for `huggingface.co` (so sentence-transformers can't download the embedding model on first run — see BUG-001).

### Reproduction steps
1. From a Cognizant corp Windows machine on the corp network (Zscaler client running)
2. `python -c "import truststore; truststore.inject_into_ssl(); import httpx; print(httpx.get('https://openrouter.ai/api/v1/models').text[:120])"`
3. Output is the Zscaler "Security Exception" HTML, not OpenRouter's model list

### Root cause
Zscaler's URL filtering policy includes `openrouter.ai` and `huggingface.co` in its blocked-domain set. The block fires *after* TLS interception, so the response Python sees is Zscaler's own page rather than a 4xx/5xx that the SDK would handle cleanly.

### Suggested fixes / workarounds
- **Preferred:** file a ServiceNow ticket via Category=Security Exception → Service=CS_Corporate Security → Service Offering="Unblock Specific URLs (Zscaler)" for `openrouter.ai` and `huggingface.co` (or specifically `https://openrouter.ai/api/v1/messages` and `https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2/*`)
- **Alternative:** point `ANTHROPIC_BASE_URL` at a Cognizant-internal Anthropic-compatible gateway if one exists in your business unit. Update `.env` accordingly
- **Alternative:** confirmed `api.anthropic.com` *is* reachable from this network (HTTP 404 with no block page) — set `ANTHROPIC_API_KEY=sk-ant-…` and remove the OpenRouter `ANTHROPIC_BASE_URL` / `ANTHROPIC_AUTH_TOKEN` entries from `.env`
- **Stopgap (in place now):** set `LLM_OFFLINE=1` in `.env`. The agent uses canned persona actions and heuristic gap detection, validating every part of the pipeline except the LLM itself

**Last verified blocked:** 2026-05-18 18:00  **Status:** OPEN — pending corp IT action


