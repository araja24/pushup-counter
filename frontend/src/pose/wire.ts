/**
 * Turning a detection into the frame shape the backend reads.
 *
 * Coordinates are copied straight through in image space: the preview is
 * mirrored with CSS, never the data (docs/adr/0006).
 */

import { LANDMARK_COUNT } from './guard'

/** One detected body point, as MediaPipe reports it. */
export interface PoseLandmark {
  x: number
  y: number
  z: number
  visibility?: number
}

/** One landmark on the wire: x, y, z, visibility. */
export type WireLandmark = [number, number, number, number]

/** One frame on the wire: the phone's clock and all 33 landmarks. */
export interface WireFrame {
  t: number
  lm: WireLandmark[]
}

export function toWireFrame(landmarks: readonly PoseLandmark[], t: number): WireFrame {
  if (landmarks.length !== LANDMARK_COUNT) {
    throw new Error(
      `toWireFrame needs all ${LANDMARK_COUNT} landmarks, got ${landmarks.length}`,
    )
  }

  return {
    t,
    lm: landmarks.map(({ x, y, z, visibility }) => [x, y, z, visibility ?? 0]),
  }
}
