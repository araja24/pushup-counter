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

### Devices used

| Row | Device | OS / browser version | Tested by | Date |
| --- | ------ | -------------------- | --------- | ---- |
| Android Chrome | pending | pending | pending | pending |
| iOS Safari | pending | pending | pending | pending |
