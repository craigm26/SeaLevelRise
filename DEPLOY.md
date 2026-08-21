# Deploy

Static site, no build step, no dependencies. Three.js is vendored in `viz/`.

## 1. Push

The repo is already initialised with one commit on `main` and `origin` set to
`https://github.com/craigm26/SeaLevelRise.git`.

```bash
git push -u origin main
```

If `origin` is missing:

```bash
git remote add origin https://github.com/craigm26/SeaLevelRise.git
git push -u origin main
```

## 2. Cloudflare Pages — dashboard (recommended)

Gives you automatic deploys on every future push.

1. Cloudflare dashboard → **Workers & Pages** → **Create** → **Pages** → **Connect to Git**
2. Select `craigm26/SeaLevelRise`
3. Build settings:

   | Field | Value |
   |---|---|
   | Framework preset | **None** |
   | Build command | *(leave empty)* |
   | Build output directory | `/` |
   | Root directory | `/` |

4. **Save and Deploy**

`wrangler.toml` already declares `pages_build_output_dir = "."`, so Cloudflare will pick the
right directory even if the dashboard field is left at its default.

## 3. Cloudflare Pages — Wrangler (alternative)

```bash
npx wrangler login                 # opens a browser
npx wrangler pages deploy . --project-name=sealevelrise
```

For CI or a headless machine, use an API token instead of `login`:

```bash
export CLOUDFLARE_API_TOKEN=...    # needs the "Cloudflare Pages: Edit" permission
export CLOUDFLARE_ACCOUNT_ID=...
npx wrangler pages deploy . --project-name=sealevelrise
```

## 4. Optional — deploy from GitHub Actions

`.github/workflows/deploy.yml` is included but **disabled by default** (it only runs on manual
dispatch). To enable automatic deploys from Actions instead of Cloudflare's own Git
integration, add two repository secrets — `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` —
and uncomment the `push:` trigger at the top of that file.

If you use Cloudflare's dashboard Git integration (step 2), you do **not** need this workflow.
Running both will deploy twice.

## Verify

After deploy, check both pages:

- `/` — the docs site. Eight charts should render. If they're missing, `data.json` didn't load.
- `/viewer.html` — the 3D visualiser. The loading bar should reach "ready" and disappear within
  a few seconds. It needs WebGL.

Both pages `fetch()` their data, so **they will not work from `file://`**. For local preview:

```bash
python3 -m http.server 8080
```

## Headers and caching

`_headers` sets security headers plus cache policy: `data.json` and the `viz/` payloads cache
for an hour, HTML always revalidates. If you change a payload and want it live immediately,
either bump the filename or purge the Cloudflare cache.

## 5. The ice monitor Worker

`ice.html` is served by Pages like everything else, but its data comes from a separate Worker
with a KV namespace and a six-hourly cron trigger. Deploy it independently:

```bash
cd ice-monitor
npx wrangler deploy
```

Live at `https://sealevelrise-ice.craigm26.workers.dev`:

| Route | Purpose |
|---|---|
| `/api/ice` | cached snapshot (what the page reads) |
| `/api/ice/history` | rolling series, ~6 months at 6-hourly |
| `/api/ice/refresh` | force a refresh now; useful after changing an adapter |

The KV namespace id is already in `wrangler.toml`. If you recreate it:

```bash
npx wrangler kv namespace create ICE   # paste the returned id into wrangler.toml
```

**Deploying the Pages site does not deploy the Worker, and vice versa.** If the tiles show
stale data after you changed an adapter, you probably deployed Pages and forgot the Worker.

Verify after deploy:

```bash
curl -s https://sealevelrise-ice.craigm26.workers.dev/api/ice/refresh | head -c 400
```

Every indicator should carry `observed`, `lagDays`, and `status`. A source in `error` is a
real failure worth chasing; a source in `unavailable` is a declared gap and is expected —
GRACE-FO is permanently `unavailable` without NASA Earthdata credentials.
