# PushForm

A mobile web app that counts push-ups live from a phone's selfie camera and tells the user whether each rep was done with acceptable form. The phone extracts body landmarks on-device; the backend decides what those landmarks mean.

## Language

### Capture

**Landmark**:
One of the 33 named body points MediaPipe reports per frame, each with normalised x, y, z and a visibility score.
_Avoid_: keypoint, joint (a joint is a body part; a landmark is the detected point for it)

**Frame**:
One set of 33 landmarks captured at one instant, stamped with the phone's clock.
_Avoid_: sample, tick

**Image Space**:
The unmirrored coordinate frame of the camera sensor. All landmarks are expressed in image space; only the on-screen preview is flipped.
_Avoid_: mirrored space, screen space

**Tracked Side**:
The side of the body (left or right) whose landmarks are currently used for angle computation, chosen by visibility.
_Avoid_: dominant side, active side

**Tracking Lost**:
The condition where the tracked side's elbow landmarks have been below the visibility floor for more than a handful of consecutive frames. Counting freezes until tracking returns.
_Avoid_: occlusion, dropout

### Counting

**Elbow Angle**:
The angle at the elbow between upper arm and forearm on the tracked side, in degrees, computed in 2D. 180° is a straight arm.

**Hip Angle**:
The angle at the hip between torso (shoulder to hip) and leg (hip to ankle) on the tracked side, in degrees. 180° is a straight body line.
_Avoid_: back angle, plank angle

**Phase**:
Which half of the movement the body is in: UP (arms extended) or DOWN (arms bent). Phase changes only when the elbow angle crosses a threshold with hysteresis.
_Avoid_: state, position

**Rep**:
One attempted push-up: the interval from entering DOWN to leaving DOWN. Time spent at the top belongs to no rep. Every rep is either counted or rejected.
_Avoid_: repetition, cycle, attempt

**Counted Rep**:
A rep judged good. Only counted reps advance the counter.
_Avoid_: valid rep, successful rep

**Rejected Rep**:
A rep with a fault. It is shown to the user with its fault and does not advance the counter.
_Avoid_: failed rep, bad rep, missed rep

**Lockout**:
Full arm extension at the top of a rep. A rep is not complete until lockout is reached.
_Avoid_: full extension, top position

**Stall**:
The condition where the elbow angle has sat between the two phase thresholds for too long, meaning the user has neither locked out nor gone down. The UI prompts for lockout.
_Avoid_: hang, pause

**Bounce**:
A DOWN phase too brief to be a genuine push-up. Bounces change phase but are never counted as reps.
_Avoid_: debounce (that is the mechanism, not the thing)

### Form

**Good Rep**:
A rep with hips and back aligned throughout, chest lowered until it nearly touches the floor, and lockout at the top. Good reps are counted reps.
_Avoid_: valid rep, clean rep, full rep

**Aligned**:
The per-frame condition that the hip angle is close enough to a straight line that the body is in plank. The skeleton is green while aligned and red while not.
_Avoid_: straight, in form

**Fault**:
The single reason a rep is rejected: partial range of motion, hip sag, or hip pike. A rep has at most one fault.
_Avoid_: flag, error, violation

**Label**:
The classifier's verdict on a rep: `good`, one of the faults, or `unlabelled` when no classifier is loaded.

**Hard Rule**:
A deterministic check that decides a rep's fault before the classifier is consulted, such as rejecting for partial range when the elbow never bent far enough, or for sag when the hips clearly dropped.
_Avoid_: safety net, heuristic

**Grey Zone**:
The band of hip deviation and elbow depth where no hard rule fires and the classifier decides the label.
_Avoid_: borderline, uncertain

### Sets and connections

**Set**:
One Start-to-Stop period, ending in a summary. A set has a counted-rep total, a rejected-rep total, and a fault breakdown.
_Avoid_: session, workout, round

**Summary**:
The record produced when a set stops: counted reps, rejected reps by fault, duration, and average rep duration.
_Avoid_: report, results

**Connection**:
One WebSocket between a phone and the backend. A connection can host several sets in a row.
_Avoid_: session, socket

### Data collection

**Recording**:
A labelled sequence of frames captured in record mode for one intended label, downloaded to the developer's device as JSON.
_Avoid_: clip, video (no video is ever stored)

**Collection Session**:
One sitting in which the developer captures several recordings under one lighting condition and camera placement.
