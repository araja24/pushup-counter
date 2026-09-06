# Mirror the display, never the data

The selfie preview is flipped horizontally so movement feels natural, but the pose landmarker runs on the unmirrored video frame and the overlay is drawn with a flip transform. Landmarks are therefore always in image space and no coordinate is ever un-mirrored in code. This removes a whole class of left/right bugs in side selection and in the signed hip deviation.
