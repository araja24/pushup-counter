# Client-side perception, server-side decisioning over a WebSocket

The phone runs pose detection and streams landmarks; a Python backend counts reps and classifies form. Alternatives were all-on-device (harder to train and test the classifier in JS, no CLI reuse) and streaming video to the server (privacy, bandwidth, latency). Splitting at the landmark boundary keeps video on the device, keeps the ML in Python where it is trained, and lets the exact same `analysis/` code serve the live app, the tests, and the dataset pipeline.
