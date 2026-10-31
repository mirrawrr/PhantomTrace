# Deploy the hackathon demo

This branch prepares deployment; it does not mean a hosted service is already
live. The normal two-terminal development workflow continues to work.

## One service, one origin

The Dockerfile builds React with `npm ci`, then copies only its built files and
the Python application into a non-root runtime. `app.production:create_app` serves
the dashboard at `/`, compiled files at `/assets`, and the existing API paths on
the same origin. Vite is not a public production server and its development proxy
is not used. The entry point respects `PORT` (default 8000).

The hosted entry point requires `MODEL_API_KEY`, `DEMO_USERNAME` and a private
`DEMO_PASSWORD` of at least 16 characters. All paths, including model endpoints,
assets and API docs, require HTTP Basic login except GET/HEAD `/health`. That
endpoint checks liveness only, not Meta credentials, billing or model readiness.
Use HTTPS for every public deployment. Responses are marked `no-store`; source
logs and reports are not persisted by this application.

This is a shared-login hackathon demo, not enterprise identity management. There
are no per-user roles, durable audit records, automatic remediation or per-user
rate limits. Keep credentials private and set provider usage limits as appropriate.
Share only synthetic evidence. A private login is distinct from the Meta API key;
never give the Meta key to judges or put either secret in public source/video.
Arrange usable judge access through the organizer's supported private channel.

## Option A: Render builds the container

No Docker installation on your laptop is required. Render can build from this
repository's Dockerfile. The included `render.yaml` requests one Free web service,
uses `/health` for liveness, prompts for the Meta key, and generates a private demo
password. Automatic deployments are off so source pushes do not deploy silently.

After the deployment PR is merged:

1. Create/sign into your own Render account and choose **New > Blueprint**.
2. Connect `mirrawrr/PhantomTrace`, selecting branch `main` and `render.yaml`.
3. Review the displayed plan. The template requests Free; do not select a paid
   plan unless you intend to. Provider terms/usage limits still apply.
4. Enter `MODEL_API_KEY` directly into Render's secret/environment field. Do not
   send it in chat, commit it, add a frontend variable or make it a Docker ARG.
5. Create the service and wait for its build/deploy result. In its environment
   settings, retrieve the generated `DEMO_PASSWORD` privately; username is `demo`.
6. Open the returned HTTPS service URL. A browser login prompt should appear.
7. Confirm unauthenticated `/health` works, then run the unbilled smoke check below.
8. Run one synthetic adaptive investigation on the hosted URL and review the
   source observations/handoff. This step is billed by Meta and is separate from
   the smoke check. A healthy container does not prove the model works.

Free Render web services sleep after 15 minutes of inactivity and can take about
one minute to wake. Open the service before recording/judging. Files are ephemeral;
this app already keeps investigations in memory and exports them to the browser.
Review current usage limits; a Free instance is a demo option, not a production
availability promise. Roll back/redeploy from the service dashboard if needed.

Official references: [Docker deployment](https://render.com/docs/docker),
[Blueprint configuration](https://render.com/docs/blueprint-spec),
[Free service limitations](https://render.com/docs/free).

## Option B: test the hosted entry point locally without Docker

Stop the existing development servers first. From the repository root:

```powershell
cd frontend
npm ci
npm run build
cd ..\backend
$env:DEMO_USERNAME = "demo"
$demoPassword = Read-Host "Private demo password (at least 16 characters)" -AsSecureString
$env:DEMO_PASSWORD = [System.Net.NetworkCredential]::new("", $demoPassword).Password
.\.venv\Scripts\python.exe -m app.serve
```

The existing `backend/.env` supplies your Meta key through the existing dotenv
loader. Do not overwrite that file with `.env.example`. Open http://127.0.0.1:8000
and log in. Only this hosted entry point requires the demo password; the original
`app.main:app` development command remains available for local use.

If Docker is already installed, an alternative from the repository root is
`docker build -t phantomtrace .`, then `docker run --rm -p 127.0.0.1:8000:8000
--env-file backend/.env -e DEMO_USERNAME -e DEMO_PASSWORD phantomtrace` after setting
those two environment variables in that terminal. Do not expose the development
server as a substitute for a hosted deployment.

## Unbilled smoke check

In another terminal at the repository root, set `DEMO_USERNAME` and set
`DEMO_PASSWORD` with the same hidden `Read-Host` method above, then run:

```powershell
.\backend\.venv\Scripts\python.exe scripts/smoke_deployment.py https://YOUR-SERVICE.onrender.com
```

Use `http://127.0.0.1:8000` for a local check. The script verifies health, rejected
anonymous access, authenticated HTML/assets and the deterministic evidence API.
It does not call Meta, print credentials or follow redirects that could forward
them to another destination. Use the service's exact origin, not a URL containing
credentials. A PASS is infrastructure evidence only; perform the live synthetic
test separately. Browser Basic credentials are cached by the browser; use a
private browser session/close it when finished rather than assuming an in-app
logout exists.

## Troubleshooting and checks

- Startup fails: confirm all three runtime variables and the built dashboard.
- Login repeats: confirm the demo username/password, not your Meta key.
- `/health` works but investigation fails: check Meta configuration/credits and
  the safe evaluation diagnostics; health intentionally makes no model request.
- Frontend points to localhost in a hosted browser: use this complete container;
  deploying only Vite's static output does not deploy the Python API.
- A run is slow: successful development runs ranged about 29-71 seconds, before
  any hosting wake time. Do not present a spinner as live tool progress.
- Public exposure or leaked demo password: rotate the hosted demo password and
  redeploy; review model usage. Avoid changing or printing the Meta key in source.

CI builds the Docker image and checks the login boundary, same-origin assets,
deterministic API, non-root user and absence of `.env` files without a real key.
Unit/API tests and the frontend build/audit remain separate checks. Frontend
dependencies are locked; existing Python requirements/base-image tags are not a
complete immutable supply-chain lock. Do not claim full reproducibility or a
security audit from these checks.
