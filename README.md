# PushForm

A mobile web app that counts push-ups live from a phone's selfie camera and tells you
whether each rep was done with acceptable form. The phone extracts body landmarks
on-device; the backend decides what those landmarks mean.

## Local development

```sh
cd backend  && uv sync && uv run uvicorn pushform.app:app --reload   # API on :8000
cd frontend && npm install && npm run dev                            # UI  on :5173
```

The backend serves `frontend/dist` at `/` once you have run `npm run build`; until then
`/` returns a placeholder page. `GET /api/health` and `GET /api/config` are always live,
and the OpenAPI docs are at `/docs`.

### Testing on a phone

Camera access needs a secure context, so `http://<your-lan-ip>:5173` will not work. Put
an HTTPS tunnel in front of the dev server and open the tunnel URL on the phone:

```sh
npx localtunnel --port 5173     # or: cloudflared tunnel --url http://localhost:5173
```

## Tests

```sh
cd backend  && uv run pytest
cd frontend && npm test
```

## Deploying

`render.yaml` describes one Render web service that builds the frontend, installs the
backend, and runs Uvicorn on the platform port — one URL for the page, the API, and the
landmark connection (see `docs/adr/0007-single-render-service.md`).

## Status

Milestone progress for v1 (see `docs/prd.md`):

- [x] **Scaffold, CI and one-service deploy** — frontend and backend build and test
      locally, GitHub Actions runs both suites, `render.yaml` exists.
- [x] **Landmark capture on the phone** — explainer, mirrored selfie preview, skeleton
      overlay from MediaPipe Pose Landmarker, and a positioning guard that gates Start
      (device confirmation pending, see `docs/device-checklist.md`).
- [ ] Rep counting over the WebSocket connection
- [ ] Form faults and the rep classifier
- [ ] Set summaries
- [ ] Recording mode for data collection

Pending — needs human:

- Confirm the GitHub Actions workflow is green on the default branch (needs a push to
  GitHub; the agent cannot observe CI).
- Create the Render service from `render.yaml` and confirm the deployed URL serves the
  placeholder page and `/api/health`.
- Run `docs/device-checklist.md` on one Android Chrome and one iOS Safari device; every
  camera and overlay row is still pending.
