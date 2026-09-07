/**
 * The Connection from the phone's side: Frames up, State, Reps and the Summary
 * back down.
 *
 * The camera produces Frames faster than the Connection needs them, and a phone
 * on a weak network must never build a queue of stale Landmarks: a Frame that
 * cannot go out now is dropped, never buffered (docs/adr/0002).
 */

import type { WireFrame } from '../pose/wire'

/** The per-Frame readout the phone draws. */
export interface StateMessage {
  type: 'state'
  reps: number
  rejected: number
  phase: 'IDLE' | 'UP' | 'DOWN'
  elbow_angle: number | null
  hip_angle: number | null
  aligned: boolean | null
  tracking: boolean
  stalled: boolean
  side: 'left' | 'right' | null
}

/** One finished Rep, counted or rejected. */
export interface RepMessage {
  type: 'rep'
  index: number
  counted: boolean
  label: string
  reason: string | null
  source: string
  min_elbow: number
  max_elbow: number
  duration_ms: number
  confidence: number | null
}

/** What a Set left behind when it stopped. */
export interface SummaryMessage {
  type: 'summary'
  reps: number
  rejected: number
  faults: Record<string, number>
  duration_ms: number
  avg_rep_ms: number
}

/** A message the backend refused. The Connection stays open. */
export interface ErrorMessage {
  type: 'error'
  code: string
  message: string
}

export type ServerMessage = StateMessage | RepMessage | SummaryMessage | ErrorMessage

/** Bytes already waiting on the socket above which Frames are dropped. */
export const BUFFER_LIMIT = 65536

/** Frames go up at up to 30 a second; the camera runs faster than that. */
export const MIN_FRAME_INTERVAL_MS = 1000 / 30

/** What became of a Frame handed to `sendFrame`. */
export type SendResult = 'sent' | 'throttled' | 'dropped' | 'closed'

export interface FrameSocketOptions {
  /** How to open the socket. Tests pass a fake in place of `WebSocket`. */
  open?: (url: string) => WebSocket
  /** The clock the frame rate is measured by. */
  now?: () => number
  /** The socket finished its handshake and is taking Frames. */
  onOpen?: () => void
  /** The socket went away, however it went. Nothing here reopens it. */
  onClose?: () => void
}

/**
 * What the phone can say about the Connection.
 *
 * `waking` is the cold-start case: the very first socket is taking so long that
 * the backend is probably still starting up.
 */
export type ConnectionStatus = 'connecting' | 'waking' | 'open' | 'reconnecting' | 'closed'

/** What a screen needs of the Connection: send Frames, run a Set, hear back. */
export interface LandmarkSocket {
  listen(listener: (message: ServerMessage) => void): () => void
  /**
   * Follow the Connection itself rather than what comes down it. Only a
   * Connection that can lose its socket and dial back has anything to say here.
   */
  listenStatus?(watcher: (status: ConnectionStatus) => void): () => void
  sendFrame(frame: WireFrame): SendResult
  start(setId: string): void
  stop(): void
  reset(): void
}

export class FrameSocket implements LandmarkSocket {
  private readonly socket: WebSocket
  private readonly now: () => number
  private readonly listeners = new Set<(message: ServerMessage) => void>()
  /** Commands sent before the socket opened. Commands wait; Frames never do. */
  private readonly pending: string[] = []
  private lastFrameAt = Number.NEGATIVE_INFINITY
  private droppedFrames = 0

  constructor(url: string, options: FrameSocketOptions = {}) {
    this.now = options.now ?? (() => Date.now())
    const open = options.open ?? ((target: string) => new WebSocket(target))
    this.socket = open(url)
    this.socket.onopen = () => {
      for (const command of this.pending.splice(0)) this.socket.send(command)
      options.onOpen?.()
    }
    this.socket.onclose = () => options.onClose?.()
    this.socket.onmessage = (event: MessageEvent) => this.receive(event.data)
  }

  /** How many Frames the Connection could not take. */
  get dropped(): number {
    return this.droppedFrames
  }

  listen(listener: (message: ServerMessage) => void): () => void {
    this.listeners.add(listener)
    return () => {
      this.listeners.delete(listener)
    }
  }

  sendFrame(frame: WireFrame): SendResult {
    if (this.socket.readyState !== WebSocket.OPEN) return 'closed'

    const at = this.now()
    if (at - this.lastFrameAt < MIN_FRAME_INTERVAL_MS) return 'throttled'

    if (this.socket.bufferedAmount > BUFFER_LIMIT) {
      this.droppedFrames += 1
      return 'dropped'
    }

    this.lastFrameAt = at
    this.socket.send(JSON.stringify(frame))
    return 'sent'
  }

  /** Begin a Set. Counting starts here; Frames were already flowing. */
  start(setId: string): void {
    this.command({ cmd: 'start', set_id: setId })
  }

  /** Pick a Set back up after the wire broke, counts and all. */
  resume(setId: string): void {
    this.command({ cmd: 'resume', set_id: setId })
  }

  /** End the Set. The Summary comes back as a message. */
  stop(): void {
    this.command({ cmd: 'stop' })
  }

  /** Throw the Set in progress away. No Summary: it never happened. */
  reset(): void {
    this.command({ cmd: 'reset' })
  }

  close(): void {
    this.listeners.clear()
    this.socket.close()
  }

  private command(command: object): void {
    const text = JSON.stringify(command)
    if (this.socket.readyState === WebSocket.OPEN) {
      this.socket.send(text)
      return
    }
    this.pending.push(text)
  }

  private receive(data: unknown): void {
    if (typeof data !== 'string') return
    let message: ServerMessage
    try {
      message = JSON.parse(data) as ServerMessage
    } catch {
      return
    }
    for (const listener of this.listeners) listener(message)
  }
}
