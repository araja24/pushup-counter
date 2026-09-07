/**
 * Runs the pose landmarker over the live video and keeps the overlay and the
 * positioning guard up to date.
 *
 * MediaPipe is pulled in with a dynamic import so the static module graph --
 * and therefore every test -- stays free of it.
 */

import { useEffect, useRef, useState } from 'react'
import type { RefObject } from 'react'

import { clearOverlay, drawSkeleton } from '../pose/draw'
import { LANDMARK_COUNT, positioningGuard } from '../pose/guard'
import type { GuardResult } from '../pose/guard'
import type { Delegate, PoseTracker } from '../pose/landmarker'

export type TrackingPhase = 'starting' | 'searching' | 'tracking' | 'failed'

export interface PoseTracking {
  /** Where the landmarker is: loading, looking for a body, or following one. */
  phase: TrackingPhase
  /** Why tracking failed, for the user to read. */
  error: string | null
  /** Which processor MediaPipe settled on, once it is running. */
  delegate: Delegate | null
  /** The latest verdict on whether the body is placed well enough to start. */
  guard: GuardResult
}

const NOT_IN_FRAME: GuardResult = { ready: false, missing: [] }

export function usePoseTracking(
  videoRef: RefObject<HTMLVideoElement | null>,
  canvasRef: RefObject<HTMLCanvasElement | null>,
): PoseTracking {
  const [phase, setPhase] = useState<TrackingPhase>('starting')
  const [error, setError] = useState<string | null>(null)
  const [delegate, setDelegate] = useState<Delegate | null>(null)
  const [guard, setGuard] = useState<GuardResult>(NOT_IN_FRAME)
  const lastMissing = useRef<string>('\u0000')

  useEffect(() => {
    let stopped = false
    let frame = 0
    let tracker: PoseTracker | null = null
    // MediaPipe rejects a timestamp that does not move forward.
    let lastTimestamp = -1

    /** Re-render only when the guide would actually read differently. */
    const publishGuard = (next: GuardResult) => {
      const key = `${next.ready}:${next.missing.join('|')}`
      if (key === lastMissing.current) return
      lastMissing.current = key
      setGuard(next)
    }

    const step = () => {
      if (stopped) return
      frame = requestAnimationFrame(step)

      const video = videoRef.current
      const canvas = canvasRef.current
      if (!tracker || !video || !canvas || video.readyState < 2 || !video.videoWidth) return

      if (canvas.width !== video.videoWidth || canvas.height !== video.videoHeight) {
        canvas.width = video.videoWidth
        canvas.height = video.videoHeight
      }
      const context = canvas.getContext('2d')
      if (!context) return

      const timestamp = Math.max(performance.now(), lastTimestamp + 1)
      lastTimestamp = timestamp

      let landmarks
      try {
        landmarks = tracker.detect(video, timestamp)
      } catch (cause) {
        stopped = true
        cancelAnimationFrame(frame)
        setError(`Pose tracking stopped: ${String(cause)}`)
        setPhase('failed')
        return
      }

      if (!landmarks || landmarks.length !== LANDMARK_COUNT) {
        clearOverlay(context)
        setPhase('searching')
        publishGuard(NOT_IN_FRAME)
        return
      }

      drawSkeleton(context, landmarks)
      setPhase('tracking')
      publishGuard(positioningGuard(landmarks.map((landmark) => landmark.visibility ?? 0)))
    }

    void (async () => {
      try {
        const { createPoseTracker } = await import('../pose/landmarker')
        const started = await createPoseTracker()
        if (stopped) {
          started.close()
          return
        }
        tracker = started
        setDelegate(started.delegate)
        setPhase('searching')
        frame = requestAnimationFrame(step)
      } catch (cause) {
        if (stopped) return
        setError(`The pose model could not be loaded: ${String(cause)}`)
        setPhase('failed')
      }
    })()

    return () => {
      stopped = true
      cancelAnimationFrame(frame)
      tracker?.close()
    }
  }, [videoRef, canvasRef])

  return { phase, error, delegate, guard }
}
