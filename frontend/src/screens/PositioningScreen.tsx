import { useEffect, useRef } from 'react'

import { lockLandscape } from '../camera/stream'
import { useIsPortrait } from '../camera/useIsPortrait'
import { usePoseTracking } from '../camera/usePoseTracking'
import type { TrackingPhase } from '../camera/usePoseTracking'

interface PositioningScreenProps {
  stream: MediaStream
  onStart: (stream: MediaStream) => void
}

/**
 * The mirrored preview with the skeleton over it, plus the guide that tells the
 * user what is not in frame yet. Start unlocks only once the guard passes.
 */
export function PositioningScreen({ stream, onStart }: PositioningScreenProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const portrait = useIsPortrait()
  const { phase, error, guard } = usePoseTracking(videoRef, canvasRef)

  useEffect(() => {
    const video = videoRef.current
    if (!video) return

    video.srcObject = stream
    void video.play().catch(() => {
      // Autoplay can be refused; the user's tap on Start plays it anyway.
    })
    return () => {
      video.srcObject = null
    }
  }, [stream])

  useEffect(() => {
    void lockLandscape()
  }, [])

  return (
    <main className="screen screen--stage">
      <div className="stage">
        {/* Mirrored for the user; the landmarker reads the unmirrored frame. */}
        <video ref={videoRef} className="stage__video" playsInline muted autoPlay />
        <canvas ref={canvasRef} className="stage__overlay" />
      </div>

      <div className="guide">
        <p role="status" className="guide__text">
          {guidance(phase, guard.missing, error)}
        </p>
        <button
          type="button"
          className="guide__start"
          disabled={!guard.ready}
          onClick={() => onStart(stream)}
        >
          Start
        </button>
      </div>

      {portrait && (
        <p role="alert" className="rotate-hint">
          Rotate your phone to landscape.
        </p>
      )}
    </main>
  )
}

function guidance(
  phase: TrackingPhase,
  missing: string[],
  error: string | null,
): string {
  if (phase === 'failed') return error ?? 'Pose tracking is unavailable on this device.'
  if (phase === 'starting') return 'Loading the pose model...'
  if (phase === 'searching') return 'Step into frame so the camera can see you.'
  if (missing.length === 0) return 'Good position. Press Start when you are ready.'
  return `Move so the camera can see: ${listParts(missing)}.`
}

/** "left shoulder, right hip and an elbow" */
function listParts(parts: string[]): string {
  if (parts.length === 1) return parts[0]
  return `${parts.slice(0, -1).join(', ')} and ${parts[parts.length - 1]}`
}
