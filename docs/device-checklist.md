# Device checklist

What has to be confirmed by hand on a real phone, because an agent run has no camera
and no device. Later tickets append rows.

Camera access needs a secure context, so test through an HTTPS tunnel to the dev server
(see the README) or against the deployed URL, not a LAN IP.

Status vocabulary: `pass`, `fail (reason)`, or `pending — needs human (no device in agent run)`.

## Capture, overlay and permissions (#3)

| # | Check | Android Chrome | iOS Safari |
| - | ----- | -------------- | ---------- |
| 1 | The explainer screen appears before any browser permission prompt. | pending — needs human (no device in agent run) | pending — needs human (no device in agent run) |
| 2 | "Turn on the camera" triggers the browser prompt; granting moves to the positioning screen. | pending — needs human (no device in agent run) | pending — needs human (no device in agent run) |
| 3 | Denying permission shows the blocked message and the button can be tried again. | pending — needs human (no device in agent run) | pending — needs human (no device in agent run) |
| 4 | The preview is the selfie camera and is mirrored: raising your right hand raises the hand on the right of the screen. | pending — needs human (no device in agent run) | pending — needs human (no device in agent run) |
| 5 | The skeleton sits on the body and follows it, with no left/right offset against the mirrored preview. | pending — needs human (no device in agent run) | pending — needs human (no device in agent run) |
| 6 | The positioning guide names the body parts that are out of frame, and the names match the user's own left and right. | pending — needs human (no device in agent run) | pending — needs human (no device in agent run) |
| 7 | Start is disabled until shoulders, hips and one full arm are in frame, then enables. | pending — needs human (no device in agent run) | pending — needs human (no device in agent run) |
| 8 | Start opens the placeholder set screen; Stop returns to positioning with the preview still live. | pending — needs human (no device in agent run) | pending — needs human (no device in agent run) |
| 9 | The page holds landscape, or shows the "rotate your phone" hint in portrait (expected on iOS Safari, which has no orientation lock). | pending — needs human (no device in agent run) | pending — needs human (no device in agent run) |
| 10 | Tracking keeps up with movement (roughly 30 fps preview, no visible lag) and the phone does not overheat in a couple of minutes. | pending — needs human (no device in agent run) | pending — needs human (no device in agent run) |
| 11 | The pose model and WASM runtime load over the network on a cold cache within a few seconds. | pending — needs human (no device in agent run) | pending — needs human (no device in agent run) |

## Live counting (#5)

| # | Check | Android Chrome | iOS Safari |
| - | ----- | -------------- | ---------- |
| 1 | Pressing Start counts reps live: five push-ups show five on the counter. | pending — needs human (no device in agent run) | pending — needs human (no device in agent run) |
| 2 | Each counted rep makes a high tone and a short buzz; the mute toggle silences the tone and is still muted after a reload. | pending — needs human (no device in agent run) | pending — needs human (no device in agent run) |
| 3 | The counter is readable from two metres away with the phone propped up in landscape. | pending — needs human (no device in agent run) | pending — needs human (no device in agent run) |
| 4 | The corner readout tracks the movement: the phase flips UP/DOWN and the elbow angle moves with the arms. | pending — needs human (no device in agent run) | pending — needs human (no device in agent run) |
| 5 | Stop shows a summary with the same count, and "Another set" counts again from zero on the same connection. | pending — needs human (no device in agent run) | pending — needs human (no device in agent run) |
| 6 | Reset mid-set puts the counter back to zero without a summary. | pending — needs human (no device in agent run) | pending — needs human (no device in agent run) |
| 7 | Counting keeps up over mobile data with no growing lag (frames are dropped, never queued). | pending — needs human (no device in agent run) | pending — needs human (no device in agent run) |

## Tracking, stalls and limits (#6)

| # | Check | Android Chrome | iOS Safari |
| - | ----- | -------------- | ---------- |
| 1 | Stepping out of the camera's view mid-set shows "Can't see you"; the counter freezes rather than counting anything, and stepping back in resumes the same rep. | pending — needs human (no device in agent run) | pending — needs human (no device in agent run) |
| 2 | Holding halfway up for a couple of seconds shows "Lock out your arms"; straightening the arms clears it. | pending — needs human (no device in agent run) | pending — needs human (no device in agent run) |
| 3 | Both cues are readable as words from two metres, not conveyed by colour alone. | pending — needs human (no device in agent run) | pending — needs human (no device in agent run) |
| 4 | Turning to face the other way mid-set does not change the count or skip a rep. | pending — needs human (no device in agent run) | pending — needs human (no device in agent run) |
| 5 | Counting is unaffected on a phone whose camera runs faster than 30 fps (frames above the limit are dropped silently, with no error on screen). | pending — needs human (no device in agent run) | pending — needs human (no device in agent run) |

### Devices used

| Row | Device | OS / browser version | Tested by | Date |
| --- | ------ | -------------------- | --------- | ---- |
| Android Chrome | pending | pending | pending | pending |
| iOS Safari | pending | pending | pending | pending |
