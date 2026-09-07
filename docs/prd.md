## Problem Statement

People doing push-ups at home or in the gym without a partner have no reliable way to know how many reps they actually did properly. Counting in your head drifts, and nobody tells you when your hips sag, when you stop short of the floor, or when you never lock your arms out at the top. Existing apps either need an install, count every wobble as a rep, or say nothing about form.

The author also needs a project that honestly demonstrates real-time systems, computer vision, and a self-trained classifier for internship applications, with a live link a recruiter can open on a phone.

## Solution

PushForm is a mobile web app opened from a URL. The user props their phone on the floor about two metres away with the screen facing them and their body side-on to the selfie camera. A skeleton overlay confirms the app can see them. They press Start and do a set. The counter advances only for good reps: hips and back aligned throughout, chest lowered until it nearly touches the floor, and lockout at the top. While the body is aligned the skeleton is green; the moment it is not, it turns red. A rejected rep is acknowledged with a low tone and a reason such as "Hips sagging" or "Go lower", and a counted rep with a high tone and a vibration. On Stop, a summary shows counted reps, rejected reps by fault, set duration, and average rep duration.

Under the hood, the phone runs a pretrained pose landmarker on-device and streams 33 landmarks per frame over a WebSocket. A Python backend runs a hysteresis state machine over the smoothed elbow angle to find reps, applies deterministic hard rules for alignment and depth, and consults a classifier trained on the author's own labelled reps for the grey zone. No video ever leaves the phone.

## User Stories

### Getting started

1. As a user, I want to open a URL on my phone and be told why the camera is needed before the permission prompt appears, so that I am not surprised by the browser dialog and do not bounce.
2. As a user, I want the app to use the selfie camera in landscape, so that I can prop the phone facing me and see the screen while I train.
3. As a user, I want the preview to be mirrored, so that moving left on the floor moves left on the screen.
4. As a user, I want a skeleton drawn over my body, so that I know the app can see me.
5. As a user, I want a positioning guide that tells me which body parts are not yet visible, so that I can adjust the phone before starting.
6. As a user, I want the Start button to stay disabled until my shoulders, hips, and at least one elbow and wrist are confidently visible, so that I do not start a set the app cannot score.
7. As a user, I want to see a "Waking up the server" state instead of a frozen screen when the backend is cold, so that I know to wait rather than reload.
8. As a user, I want the live elbow angle and phase shown small in a corner before I start, so that I can check the app is reading my arm correctly.

### Counting

9. As a user, I want the counter to be large enough to read from two metres away, so that I can see it mid-set without leaning in.
10. As a user, I want only good reps to advance the counter, so that the number means push-ups done properly.
11. As a user, I want a rep to require full lockout at the top before it can complete, so that half-extensions never count.
12. As a user, I want to be prompted to lock out my arms if I hover between up and down for too long, so that I understand why the counter has not moved.
13. As a user, I want a rapid bounce at the bottom not to count as a rep, so that cheating the machine is not possible by accident.
14. As a user, I want the count to keep working if the camera briefly loses my elbow at the bottom of a rep, so that the hardest part of the movement is not where reps get lost.
15. As a user, I want the app to tell me when it cannot see me, so that I can reposition instead of wondering why nothing is counting.
16. As a user, I want the app to pick whichever side of my body it can see best and not flip mid-rep, so that the angle readout does not jump.
17. As a user, I want a high tone and a short vibration on each counted rep, so that I do not have to look at the screen.
18. As a user, I want a small rejected tally beside the main counter, so that I can see a rejected rep was noticed rather than swallowed.
19. As a user, I want the counter to survive a brief network drop, so that a Wi-Fi hiccup does not zero my set.

### Form feedback

20. As a user, I want the skeleton to turn red the instant my hips sag or pike, so that I can correct my back while still in the rep.
21. As a user, I want the skeleton to stay red until the end of a rep that has already been faulted, so that a brief sag does not flicker past unnoticed.
22. As a user, I want a rejected rep to play a low tone and show its reason for two seconds, so that I know both that it was rejected and why.
23. As a user, I want to be told "Go lower" at the end of a rep where my chest did not get close enough to the floor, so that I know to increase my depth.
24. As a user, I want the form check to be strict but not punitive, so that borderline reps are not thrown away on a coin flip.
25. As a user, I want a rep that was green throughout but judged faulty by the classifier to carry a specific reason, so that I am never rejected without explanation.
26. As a user, I want to be able to mute the tones, so that I can train quietly, and I want that choice remembered.

### Set summary

27. As a user, I want to press Stop and see counted reps, rejected reps by fault, set duration, and average rep duration, so that I can track quality and not just quantity.
28. As a user, I want to start another set without reloading the page, so that a workout of several sets is smooth.
29. As a user, I want a Reset that abandons the current set without a summary, so that a false start does not pollute my numbers.

### Threshold tuning

30. As a user, I want the up and down thresholds to be adjustable between sets, so that the defaults can be adapted to my body if they are wrong for me.
31. As a user, I want threshold changes to be refused mid-set, so that a set is scored consistently from start to finish.

### Developer: data collection

32. As a developer, I want a hidden record mode reached by a query flag, so that ordinary users never see it.
33. As a developer, I want to choose the intended label for a recording before it starts, so that every rep in the recording is labelled by the set I intended to do.
34. As a developer, I want a countdown before recording begins, so that I can get into position.
35. As a developer, I want the recording downloaded to my device as JSON named by label and timestamp, so that nothing is stored on the server and I can delete it after import.
36. As a developer, I want a script that runs the production state machine over a recording and slices it into reps, so that training windows are defined exactly as they will be at inference.
37. As a developer, I want segmentation to treat every completed movement as a rep regardless of the hard rules, so that faulted recordings still yield training examples.
38. As a developer, I want a script that turns per-rep windows into a feature table, so that I can train on tabular data.
39. As a developer, I want a training script that reports cross-validated metrics and a held-out day, writes the model, the ordered feature list, and a metrics file, so that training and inference cannot drift and results are auditable.
40. As a developer, I want the model version and metrics surfaced by the health endpoint, so that I can confirm which model is deployed.

### Developer: architecture and testing

41. As a developer, I want the analysis package to have no web dependencies, so that I can unit test it with synthetic landmark sequences and run it from a CLI.
42. As a developer, I want one entry point that takes a frame and returns events, so that the WebSocket handler, the tests, and the segmentation script all exercise identical logic.
43. As a developer, I want all thresholds, windows, and the classifier confidence floor centralised in one configuration module, so that tuning is one edit.
44. As a developer, I want a working counter and hard-rule form feedback before any model exists, so that the app is demoable at the second milestone.
45. As a developer, I want a test that loads the shipped model and checks four canonical feature vectors, so that artefact and feature-list drift is caught in CI.
46. As a developer, I want continuous integration running the Python and frontend tests on every push, so that the main branch is always green.
47. As a developer, I want the whole app deployed as one service at one URL, so that there is no cross-origin WebSocket setup and one link to share.

### Interviewer

48. As an interviewer, I want to open a link on my phone and see the app working within thirty seconds, so that I can evaluate the project quickly.
49. As an interviewer, I want a README with a GIF, an architecture diagram, and links to the ADRs, so that I can understand the design without running it.

## Implementation Decisions

### Repository and tooling

- One repository with a `frontend` directory (Vite, React, TypeScript, npm) and a `backend` directory (Python 3.12). The Python package is named `pushform`.
- Python dependencies are managed with uv and a lockfile locally; a plain requirements file is exported for Render so deployment stays boring.
- GitHub Actions runs pytest and the frontend tests on every push from the first commit.
- The PRD lives under the docs directory. The glossary is the root CONTEXT.md and the ADRs live under docs/adr. All code, issues, and tests use the glossary's vocabulary: Set, Connection, Rep, Counted Rep, Rejected Rep, Fault, Label, Hard Rule, Grey Zone, Aligned, Stall, Bounce, Tracked Side, Tracking Lost. "Session" and "flag" are not used.

### Capture (frontend)

- The selfie camera is requested at landscape orientation targeting 30 fps. The pose landmarker (MediaPipe Tasks Vision, lite model, GPU delegate with CPU fallback) runs on the unmirrored video frame. Only the overlay canvas is drawn with a horizontal flip. No coordinate is ever un-mirrored in code (ADR-0006).
- Each frame sends 33 landmarks as `[x, y, z, visibility]` in image space with a client timestamp in epoch milliseconds. Angles are computed in 2D on the backend; z is transmitted so recordings keep it.
- Frames are sent at up to 30 per second. If the socket is congested, frames are dropped, never queued.
- Frames stream from the moment the connection opens, not from Start, so the pre-start angle readout uses the backend's angle code and the Render instance is warmed.
- The positioning guard runs in the frontend from landmark visibility alone: shoulders, hips, and at least one elbow and wrist above 0.6 visibility enable Start.
- Overlay colour is driven by the `aligned` field of the latest state message from the backend: green when aligned, red when not. Once a rep is faulted, the backend reports not-aligned until that rep ends, so the frontend needs no memory of its own.

### Rep detection (analysis package)

- A single orchestrator takes one frame and returns a list of events. It is the only entry point used by the WebSocket handler, the tests, and the segmentation script. It has no web imports.
- Elbow angle is computed for both sides each frame. The Tracked Side is the side with higher mean landmark visibility over the last 10 frames, re-evaluated only while in UP. Switching resets the median filter. The tracked elbow angle is median-filtered over 5 frames.
- Phase is UP or DOWN with hysteresis: enter DOWN below 95 degrees, leave DOWN above 155 degrees, no change in between. A set starts in UP and requires a real UP-to-DOWN transition before anything can count. Defaults are overridable per Connection between Sets only.
- A Rep is the interval from entering DOWN to leaving DOWN. A rep completes on the DOWN-to-UP transition, which is also lockout. A DOWN phase shorter than 400 ms is a Bounce: the phase still changes but no rep event is emitted.
- Stall: if the smoothed elbow angle stays between the two thresholds for more than 1.5 s, a stall event is emitted once, and cleared when the angle leaves the band.
- Tracking Lost: if the tracked side's elbow landmarks are below 0.6 visibility for more than 5 consecutive frames, the last good angle is held for those 5 frames, then the machine freezes in its current phase and emits a tracking-lost event. When tracking returns the rep continues. Frames received while a Connection is reconnecting are treated the same way.
- Per-rep statistics tracked: minimum and maximum elbow angle, duration, time from DOWN entry to the minimum angle and from the minimum to DOWN exit, hip angle statistics, and the features below.

### Form assessment (analysis package)

- Hip angle is shoulder-hip-ankle on the Tracked Side. Its signed deviation from 180 degrees uses the sign of the cross product of the shoulder-to-hip and hip-to-ankle vectors, so sag is negative and pike positive regardless of which way the user faces. Tests cover both facings.
- Aligned is a per-frame condition: absolute signed hip deviation within the alignment tolerance (default 20 degrees). Emitted on every state message.
- Hard Rules, evaluated at rep end, in order: hip sag if the mean signed deviation during the rep is below minus 20 degrees; hip pike if above plus 20 degrees; partial range of motion if the minimum elbow angle exceeds 110 degrees. The first that fires is the Fault. Hard rules work with no model loaded.
- Grey Zone: if no hard rule fires and a classifier is loaded, the rep's feature vector is classified. A fault label is applied only when its predicted probability is at least 0.7 (the confidence floor); otherwise the rep is labelled good. If no classifier is loaded, the label is `unlabelled` and the rep counts.
- A rep with a Fault is a Rejected Rep. A rep with label good or unlabelled is a Counted Rep. Only counted reps advance the counter (ADR-0008, ADR-0009).
- Features per rep, all lengths normalised by torso length: minimum elbow, maximum elbow, range, duration, down time, up time, hip mean, min, max, standard deviation, mean signed hip deviation, mean body-line error (perpendicular distance of hip from the shoulder-ankle line normalised by shoulder-ankle length), head drop at the bottom of the rep, and horizontal wrist-to-shoulder offset.

### Sets and Connections (backend)

- One Connection holds at most one active Set plus a small in-memory store of recently orphaned sets keyed by set id. A Set is created by the start command, which carries a client-generated set id. Stop ends the set and emits a summary. Reset abandons it without a summary.
- Reconnect: a new Connection sending a resume command with a known set id within 10 s of the old Connection dropping adopts that Set. Orphans older than 10 s are discarded silently.
- Frames above 40 per second per Connection are dropped silently. Any message over 8 KB closes the Connection with a policy violation close code. The WebSocket upgrade checks Origin against the serving host.
- Set summaries are plain in-memory records shaped so they can be persisted later. No database in this scope.

### Wire contract

- Client to server, per frame: `{"t": <epoch ms>, "lm": [[x, y, z, v] x 33]}`.
- Client to server, control: `{"cmd": "start", "set_id": <uuid>}`, `{"cmd": "stop"}`, `{"cmd": "reset"}`, `{"cmd": "resume", "set_id": <uuid>}`, `{"cmd": "config", "down_threshold": 95, "up_threshold": 155}`.
- Server to client, state, throttled to 15 per second: `{"type": "state", "reps": n, "rejected": n, "phase": "IDLE" | "UP" | "DOWN", "elbow_angle": deg, "hip_angle": deg, "aligned": bool, "tracking": bool, "stalled": bool, "side": "left" | "right"}`. Phase is IDLE before Start.
- Server to client, on each completed rep: `{"type": "rep", "index": n, "counted": bool, "label": "good" | "partial_rom" | "hip_sag" | "hip_pike" | "unlabelled", "reason": <user-facing text or null>, "source": "hard_rule" | "classifier" | "none", "min_elbow": deg, "max_elbow": deg, "duration_ms": n, "confidence": float or null}`. Index counts every completed rep, counted or not.
- Server to client, on stop: `{"type": "summary", "reps": n, "rejected": n, "faults": {"partial_rom": n, "hip_sag": n, "hip_pike": n}, "duration_ms": n, "avg_rep_ms": n}`.
- Server to client, on error: `{"type": "error", "code": <string>, "message": <string>}`, for instance a config command during an active Set.
- REST: health (liveness, model version, metrics, uptime) and config (current default thresholds), both with Pydantic models and OpenAPI docs. No recordings endpoint and no sessions endpoints in this scope.

### Feedback (frontend)

- The counter shows counted reps at 120 px minimum in landscape, with the rejected tally small beside it, and an ARIA live region announcing the count.
- Counted rep: high tone via Web Audio plus a 50 ms vibration where supported. Rejected rep: low tone plus the same vibration, and the reason text shown for 2 s. Partial range also flashes the skeleton red once, since depth is known only at rep end. The mute toggle silences both tones and persists in local storage. Tones are on by default.
- Stall shows "Lock out your arms". Tracking lost shows "Can't see you".
- Screens: pre-permission explainer, positioning and ready screen, live screen, summary screen, and the hidden record screen. The summary offers "Another set", which starts a new Set on the same Connection.
- The WebSocket URL is derived from the page location. Reconnect uses exponential backoff and sends resume with the current set id.

### Data collection and training

- Record mode is reached by a query flag. The developer picks the intended label, gets a countdown, records, stops, and the browser downloads a JSON file named by label and timestamp containing the frame sequence and the label. Nothing is posted to the server. Recordings are deleted from the device after import into the local data directory, which is gitignored.
- The segmentation script runs the production orchestrator over a recording with the form gate disabled, so every completed rep becomes a window carrying the recording's label.
- The dataset script writes a feature table with one row per rep, using the same feature code as inference.
- The training script fits a standardised logistic regression baseline and a random forest or gradient boosting model, picks by cross-validated macro-F1, reports accuracy, macro-F1 and a confusion matrix from stratified 5-fold cross-validation plus a held-out collection day, and writes the model pipeline, the ordered feature list, and a metrics file. Acceptance: macro-F1 at least 0.85 on cross-validation and at least 0.75 on the held-out day.
- The backend loads the model once at startup if present, records its version, and runs with hard rules only if absent.
- Collection protocol: about 40 reps per class across at least 3 collection sessions on different days and at least 2 lighting conditions, facing left and right in roughly equal measure, one intended label per recording, full push-ups only.

### Deployment

- One Render web service. The build installs the frontend, builds it, and installs the Python requirements. FastAPI mounts the built frontend as static files and serves the API and WebSocket (ADR-0007). A "Waking up the server" state covers cold starts.
- Local development uses the Vite dev server with host exposure plus an HTTPS tunnel so the phone gets a secure context for camera access.

## Testing Decisions

A good test drives a seam from the outside with realistic input and asserts only on what comes back out. It never reaches into a filter's buffer or a state machine's private fields. For this project the realistic input is a synthetic landmark sequence and the output is a list of events or a sequence of messages.

### Seam 1, primary: the analysis orchestrator

Tests build synthetic push-up cycles with a generator that controls elbow range, hip deviation, facing direction, noise, frame rate, and dropped frames, feed them frame by frame to the orchestrator, and assert the events. This seam carries the bulk of the suite:

- Angle math: known triangles give known angles; signed hip deviation has the right sign for both facings and for sag versus pike.
- Counting: N clean cycles yield N counted reps; angles sitting inside the hysteresis band never transition; a set beginning at the bottom does not count its first ascent.
- Bounce: a DOWN phase under 400 ms changes phase but emits no rep.
- Stall: hovering between thresholds for more than 1.5 s emits one stall event, which clears on leaving the band.
- Tracking Lost: short visibility gaps at the bottom of a rep do not lose the rep; a long gap freezes phase and emits tracking-lost; the rep completes after tracking returns.
- Tracked Side: the more visible side is selected; the side does not switch during DOWN; a switch in UP resets smoothing without emitting a rep.
- Hard Rules: sag, pike, and partial-range cycles produce rejected reps with the right fault, in the documented order of precedence, with no model loaded.
- Grey Zone: with a stub classifier injected, a fault at 0.69 probability counts and at 0.70 rejects; with no classifier the label is unlabelled and the rep counts.
- Aligned: the per-frame flag flips red at the alignment tolerance and stays red until rep end once the rep is faulted.
- Features: golden tests that a fixed synthetic rep produces a fixed feature vector, and that the feature order matches the shipped ordered feature list.
- Sets: start, stop, and reset produce the right summary or none; config is refused during an active Set.
- Model drift guard: the shipped model predicts the expected class for four hand-built canonical vectors.
- Segmentation: running the orchestrator with the gate disabled over a synthetic faulted recording yields one window per completed rep.

### Seam 2, thin: the WebSocket endpoint

FastAPI's test client opens the socket, sends start, streams a synthetic set, sends stop, and asserts the ordered sequence of state, rep, and summary messages and their shapes. Further cases: resume within 10 s adopts the Set and the count continues; resume after 10 s starts fresh; an oversized message closes the socket; a config command during a Set returns an error message; health and config endpoints return their documented shapes.

### Seam 3, thin: the frontend socket client and serialiser

Vitest with a fake WebSocket: frame JSON has the documented shape; frames are dropped when the buffer is full rather than queued; reconnect backs off exponentially and sends resume with the current set id; the mute preference round-trips through local storage.

### Not automated

Camera permission, the landmarker, the canvas overlay, tones, and vibration are covered by a written device checklist run on one Android Chrome and one iOS Safari device before each milestone.

### Prior art

None in this repository; it is empty. The pattern follows the author's earlier project Sada: pure analysis package, synthetic inputs, assertions on outputs only. Target at least 80 tests, no network access, no binary fixtures; the model drift test uses the committed model file, which is small.

## Out of Scope

- Knee push-ups and any exercise mode selector. Full push-ups only; the hip angle is shoulder-hip-ankle.
- Other exercises, front-on or overhead orientation, multi-person tracking.
- Persisting Sets to a database and the sessions endpoints. Summaries are in-memory records shaped for later persistence.
- A calibration step that personalises thresholds.
- A user-facing export of landmark data or a rendered skeleton video.
- A fifth `no_lockout` class. Lockout is enforced by counting, not by classification.
- Running the classifier on the phone.
- Native apps, accounts, social features, coaching programmes.
- Uploading recordings to the server.

## Further Notes

- Milestone order follows the PRD: skeleton on phone, live counter, data collected, classifier trained, form feedback live, shipped. Because hard rules run without a model, form feedback is largely present from the second milestone; the fifth milestone becomes "classifier live in the grey zone".
- Resume claims stay gated on milestones: "real-time push-up counter" after the live counter; "trained a form classifier on a self-collected dataset" only after the classifier meets the acceptance metrics.
- The two-tone, red-skeleton design means the app is usable without looking at the screen and without reading English, which matters at two metres on the floor.
- Relevant ADRs: 0001 through 0009 under docs/adr. Any ticket that contradicts one must say so explicitly.
