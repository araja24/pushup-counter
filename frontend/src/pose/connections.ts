/**
 * The pairs of landmarks the skeleton overlay joins with a line.
 *
 * Kept here rather than taken from MediaPipe's own `POSE_CONNECTIONS` so the
 * drawing code stays free of `@mediapipe/tasks-vision`, and so the face mesh
 * lines -- noise for a push-up -- are left out.
 */

import { LANDMARK } from './guard'

const LEFT_KNEE = 25
const RIGHT_KNEE = 26
const LEFT_ANKLE = 27
const RIGHT_ANKLE = 28
const LEFT_HEEL = 29
const RIGHT_HEEL = 30
const LEFT_FOOT = 31
const RIGHT_FOOT = 32

export const POSE_CONNECTIONS: ReadonlyArray<readonly [number, number]> = [
  // Torso
  [LANDMARK.leftShoulder, LANDMARK.rightShoulder],
  [LANDMARK.leftShoulder, LANDMARK.leftHip],
  [LANDMARK.rightShoulder, LANDMARK.rightHip],
  [LANDMARK.leftHip, LANDMARK.rightHip],
  // Arms
  [LANDMARK.leftShoulder, LANDMARK.leftElbow],
  [LANDMARK.leftElbow, LANDMARK.leftWrist],
  [LANDMARK.rightShoulder, LANDMARK.rightElbow],
  [LANDMARK.rightElbow, LANDMARK.rightWrist],
  // Legs
  [LANDMARK.leftHip, LEFT_KNEE],
  [LEFT_KNEE, LEFT_ANKLE],
  [LEFT_ANKLE, LEFT_HEEL],
  [LEFT_HEEL, LEFT_FOOT],
  [LANDMARK.rightHip, RIGHT_KNEE],
  [RIGHT_KNEE, RIGHT_ANKLE],
  [RIGHT_ANKLE, RIGHT_HEEL],
  [RIGHT_HEEL, RIGHT_FOOT],
]
