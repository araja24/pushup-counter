/**
 * Drawing the skeleton over the mirrored preview.
 *
 * The landmarks handed in are in image space and are never altered; the flip
 * that makes the overlay line up with the mirrored video is a canvas transform
 * (docs/adr/0006).
 */

import { POSE_CONNECTIONS } from './connections'
import { VISIBILITY_FLOOR } from './guard'
import type { PoseLandmark } from './wire'

const BONE_COLOUR = '#5ef2b0'
const JOINT_COLOUR = '#ffffff'
const BONE_WIDTH = 4
const JOINT_RADIUS = 5

/** Wipe the overlay, e.g. when no body is detected. */
export function clearOverlay(ctx: CanvasRenderingContext2D): void {
  ctx.setTransform(1, 0, 0, 1, 0, 0)
  ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height)
}

export function drawSkeleton(
  ctx: CanvasRenderingContext2D,
  landmarks: readonly PoseLandmark[],
): void {
  const { width, height } = ctx.canvas
  clearOverlay(ctx)

  // Mirror the drawing only: x = width - x, applied by the transform.
  ctx.setTransform(-1, 0, 0, 1, width, 0)

  const inFrame = (landmark: PoseLandmark | undefined) =>
    landmark !== undefined && (landmark.visibility ?? 0) >= VISIBILITY_FLOOR

  ctx.strokeStyle = BONE_COLOUR
  ctx.lineWidth = BONE_WIDTH
  ctx.lineCap = 'round'
  for (const [from, to] of POSE_CONNECTIONS) {
    const start = landmarks[from]
    const end = landmarks[to]
    if (!inFrame(start) || !inFrame(end)) continue

    ctx.beginPath()
    ctx.moveTo(start.x * width, start.y * height)
    ctx.lineTo(end.x * width, end.y * height)
    ctx.stroke()
  }

  ctx.fillStyle = JOINT_COLOUR
  for (const landmark of landmarks) {
    if (!inFrame(landmark)) continue

    ctx.beginPath()
    ctx.arc(landmark.x * width, landmark.y * height, JOINT_RADIUS, 0, Math.PI * 2)
    ctx.fill()
  }
}
