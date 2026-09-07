/**
 * Whether the body is placed well enough for a set to begin.
 *
 * Counting needs both shoulders, both hips, and one complete arm: the elbow
 * angle is measured on a tracked side, so an elbow on one side and a wrist on
 * the other is no use. Names are anatomical (the user's own left and right),
 * which is also how the mirrored preview reads back to them.
 */

/** A landmark at or above this visibility score is treated as in frame. */
export const VISIBILITY_FLOOR = 0.6

/** The MediaPipe landmark indices the guard cares about. */
export const LANDMARK = {
  leftShoulder: 11,
  rightShoulder: 12,
  leftElbow: 13,
  rightElbow: 14,
  leftWrist: 15,
  rightWrist: 16,
  leftHip: 23,
  rightHip: 24,
} as const

/** The number of landmarks MediaPipe reports per frame. */
export const LANDMARK_COUNT = 33

export interface GuardResult {
  /** True when every required landmark is in frame and a set may start. */
  ready: boolean
  /** Body parts to bring into frame, phrased for the positioning guide. */
  missing: string[]
}

const TORSO: ReadonlyArray<readonly [number, string]> = [
  [LANDMARK.leftShoulder, 'left shoulder'],
  [LANDMARK.rightShoulder, 'right shoulder'],
  [LANDMARK.leftHip, 'left hip'],
  [LANDMARK.rightHip, 'right hip'],
]

export function positioningGuard(visibilities: readonly number[]): GuardResult {
  if (visibilities.length !== LANDMARK_COUNT) {
    throw new Error(
      `positioningGuard needs all ${LANDMARK_COUNT} landmark visibilities, got ${visibilities.length}`,
    )
  }

  const visible = (index: number) => visibilities[index] >= VISIBILITY_FLOOR

  const missing = TORSO.filter(([index]) => !visible(index)).map(([, name]) => name)
  missing.push(...missingArmParts(visible))

  return { ready: missing.length === 0, missing }
}

/** What the user must bring into frame before some one side has both elbow and wrist. */
function missingArmParts(visible: (index: number) => boolean): string[] {
  const leftArm = visible(LANDMARK.leftElbow) && visible(LANDMARK.leftWrist)
  const rightArm = visible(LANDMARK.rightElbow) && visible(LANDMARK.rightWrist)
  if (leftArm || rightArm) return []

  const anyElbow = visible(LANDMARK.leftElbow) || visible(LANDMARK.rightElbow)
  const anyWrist = visible(LANDMARK.leftWrist) || visible(LANDMARK.rightWrist)

  // Both are in frame but on opposite sides, so neither one alone is missing.
  if (anyElbow && anyWrist) return ['an elbow and a wrist on the same side']

  const parts: string[] = []
  if (!anyElbow) parts.push('an elbow')
  if (!anyWrist) parts.push('a wrist')
  return parts
}
