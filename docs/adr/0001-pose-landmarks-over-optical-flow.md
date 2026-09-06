# Pose landmarks over optical-flow frame classification

The reference project classifies raw video motion with a CNN over optical flow and never locates joints. We instead run a pretrained pose landmarker on-device and do all reasoning on joint angles. Landmarks are explainable (every decision names an angle), robust to background and lighting, about 130 floats per frame so they fit over a WebSocket, and they make form feedback possible, which optical flow cannot give.
