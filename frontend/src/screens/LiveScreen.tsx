import { useEffect, useRef, useState } from 'react'

import { playHighTone } from '../audio/tones'
import { usePoseTracking } from '../camera/usePoseTracking'
import { cueFor } from './cues'
import type { LandmarkSocket, SummaryMessage } from '../net/socket'
import { toWireFrame } from '../pose/wire'
import { loadMuted, saveMuted } from '../prefs/mute'

interface LiveScreenProps {
  stream: MediaStream
  socket: LandmarkSocket
  /** The Set stopped and the backend summarised it. */
  onFinished: (summary: SummaryMessage) => void
}

const VIBRATE_MS = 50

/** How long a refusal from the backend stays on screen before it gets out of the way. */
export const NOTICE_MS = 2000

/**
 * The Set in progress: the count, and the feedback that reaches a user who is
 * face-down on the floor and cannot read anything -- a tone and a buzz per
 * counted Rep. Every number here comes from the backend; the phone counts
 * nothing of its own (docs/adr/0002).
 */
export function LiveScreen({ stream, socket, onFinished }: LiveScreenProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const [reps, setReps] = useState(0)
  const [rejected, setRejected] = useState(0)
  const [phase, setPhase] = useState('IDLE')
  const [elbowAngle, setElbowAngle] = useState<number | null>(null)
  /** What the backend cannot do for the user right now, in words. */
  const [cue, setCue] = useState<string | null>(null)
  const [muted, setMuted] = useState(loadMuted)
  const [stopping, setStopping] = useState(false)
  const [notice, setNotice] = useState<string | null>(null)
  // The message listener is set up once; it reads the live choice from a ref.
  const silent = useRef(muted)
  useEffect(() => {
    silent.current = muted
  }, [muted])

  usePoseTracking(videoRef, canvasRef, (landmarks, timestampMs) => {
    socket.sendFrame(toWireFrame(landmarks, Math.round(timestampMs)))
  })

  useEffect(() => {
    const video = videoRef.current
    if (!video) return

    video.srcObject = stream
    void video.play()?.catch(() => {
      // Already playing from the positioning screen on most browsers.
    })
    return () => {
      video.srcObject = null
    }
  }, [stream])

  useEffect(() => {
    const stopListening = socket.listen((message) => {
      if (message.type === 'state') {
        setReps(message.reps)
        setRejected(message.rejected)
        setPhase(message.phase)
        setElbowAngle(message.elbow_angle)
        setCue(cueFor(message))
        return
      }
      if (message.type === 'rep' && message.counted) {
        if (!silent.current) playHighTone()
        navigator.vibrate?.(VIBRATE_MS)
        return
      }
      if (message.type === 'summary') {
        onFinished(message)
        return
      }
      if (message.type === 'error') setNotice(message.message)
    })

    socket.start(newSetId())
    return stopListening
  }, [socket, onFinished])

  useEffect(() => {
    if (notice === null) return
    const clearing = setTimeout(() => setNotice(null), NOTICE_MS)
    return () => clearTimeout(clearing)
  }, [notice])

  /** Abandon this Set and begin another straight away, on the same Connection. */
  const restart = () => {
    socket.reset()
    socket.start(newSetId())
    setReps(0)
    setRejected(0)
    setCue(null)
  }

  const stop = () => {
    setStopping(true)
    socket.stop()
  }

  const toggleMute = () => {
    const next = !muted
    setMuted(next)
    saveMuted(next)
  }

  return (
    <main className="screen screen--stage">
      <div className="stage">
        {/* Mirrored for the user; the landmarker reads the unmirrored frame. */}
        <video ref={videoRef} className="stage__video" playsInline muted autoPlay />
        <canvas ref={canvasRef} className="stage__overlay" />

        <p className="count" aria-hidden="true">
          {reps}
        </p>
        <p className="visually-hidden" aria-live="polite">
          {reps} {reps === 1 ? 'rep' : 'reps'}
        </p>
        <p className="tally">{rejected} rejected</p>
        <p className="readout">{readout(phase, elbowAngle)}</p>
        {/* Stays up for as long as the condition does: it is a live state,
            not a passing message like the notice below it. */}
        {cue !== null && (
          <p role="status" className="cue">
            {cue}
          </p>
        )}
        {notice !== null && (
          <p role="status" className="notice">
            {notice}
          </p>
        )}
      </div>

      <div className="guide">
        <button type="button" onClick={toggleMute} aria-pressed={muted}>
          {muted ? 'Unmute' : 'Mute'}
        </button>
        <button type="button" onClick={restart}>
          Reset
        </button>
        <button type="button" onClick={stop} disabled={stopping}>
          Stop
        </button>
      </div>
    </main>
  )
}

/** "DOWN 82°" -- the Phase and Elbow Angle the backend last reported. */
function readout(phase: string, elbowAngle: number | null): string {
  if (elbowAngle === null) return phase
  return `${phase} ${Math.round(elbowAngle)}°`
}

function newSetId(): string {
  return globalThis.crypto?.randomUUID?.() ?? `set-${Date.now()}`
}
