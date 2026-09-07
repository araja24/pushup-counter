/**
 * The Connection that survives a Wi-Fi hiccup.
 *
 * A phone on a home network drops its socket without warning, and the Set in
 * progress must not go with it: the backend parks the Set for ten seconds, so
 * this dials back and the first thing it says on the new socket is `resume` with
 * the set id it was already counting. Attempts are spaced out so a backend that
 * is genuinely down is not hammered.
 *
 * Everything that waits -- the backoff, and the delay before the phone admits
 * the server is still waking up -- runs on injected timers, so a test drives it
 * without real time passing.
 *
 *     const connection = new ReconnectingSocket(frameSocketUrl(window.location))
 *     connection.listenStatus((status) => setStatus(status))
 */

import { FrameSocket } from './socket'
import type { ConnectionStatus, LandmarkSocket, SendResult, ServerMessage } from './socket'
import { WAKING_MS } from './wakeup'
import type { TimerHandle } from './wakeup'
import type { WireFrame } from '../pose/wire'

export { WAKING_MS }

/** How long the phone waits before its first attempt to dial back. */
export const RECONNECT_BASE_MS = 500

/** The longest it ever waits between attempts, however long the backend is away. */
export const RECONNECT_CAP_MS = 8000

export interface ReconnectingSocketOptions {
  /** How to open a socket. Tests pass a fake in place of `WebSocket`. */
  open?: (url: string) => WebSocket
  /** The clock the frame rate is measured by. */
  now?: () => number
  setTimer?: (run: () => void, ms: number) => TimerHandle
  clearTimer?: (handle: TimerHandle) => void
  /** How long the first socket may take to open before the phone says so. */
  wakingMs?: number
}

export class ReconnectingSocket implements LandmarkSocket {
  private readonly url: string
  private readonly options: ReconnectingSocketOptions
  private readonly setTimer: (run: () => void, ms: number) => TimerHandle
  private readonly clearTimer: (handle: TimerHandle) => void
  private readonly wakingMs: number
  private readonly listeners = new Set<(message: ServerMessage) => void>()
  private readonly watchers = new Set<(status: ConnectionStatus) => void>()
  private socket: FrameSocket
  /** The Set the phone is counting, and the one a new socket must resume. */
  private setInProgress: string | null = null
  private attempts = 0
  private state: ConnectionStatus = 'connecting'
  private retry: TimerHandle | null = null
  private slowOpen: TimerHandle | null = null

  constructor(url: string, options: ReconnectingSocketOptions = {}) {
    this.url = url
    this.options = options
    this.setTimer = options.setTimer ?? ((run, ms) => setTimeout(run, ms))
    this.clearTimer = options.clearTimer ?? ((handle) => clearTimeout(handle))
    this.wakingMs = options.wakingMs ?? WAKING_MS
    this.socket = this.dial(true)
  }

  /** What the phone should be telling the user about the Connection. */
  get status(): ConnectionStatus {
    return this.state
  }

  listen(listener: (message: ServerMessage) => void): () => void {
    this.listeners.add(listener)
    return () => {
      this.listeners.delete(listener)
    }
  }

  /** Follow the Connection itself, rather than what comes down it. */
  listenStatus(watcher: (status: ConnectionStatus) => void): () => void {
    this.watchers.add(watcher)
    return () => {
      this.watchers.delete(watcher)
    }
  }

  sendFrame(frame: WireFrame): SendResult {
    return this.socket.sendFrame(frame)
  }

  start(setId: string): void {
    this.setInProgress = setId
    this.socket.start(setId)
  }

  stop(): void {
    this.setInProgress = null
    this.socket.stop()
  }

  reset(): void {
    this.setInProgress = null
    this.socket.reset()
  }

  /** Shut the Connection for good. Nothing dials back after this. */
  close(): void {
    this.cancel()
    this.report('closed')
    this.listeners.clear()
    this.socket.close()
  }

  private dial(first: boolean): FrameSocket {
    const socket = new FrameSocket(this.url, {
      open: this.options.open,
      now: this.options.now,
      onOpen: () => this.opened(),
      onClose: () => this.dropped(),
    })
    socket.listen((message) => {
      for (const listener of [...this.listeners]) listener(message)
    })
    // Queued before anything else, so the backend adopts the Set before it sees
    // a single Frame.
    if (this.setInProgress !== null) socket.resume(this.setInProgress)
    if (first) {
      this.slowOpen = this.setTimer(() => this.report('waking'), this.wakingMs)
    }
    return socket
  }

  private opened(): void {
    this.attempts = 0
    this.cancelSlowOpen()
    this.report('open')
  }

  private dropped(): void {
    if (this.state === 'closed') return
    this.cancelSlowOpen()
    this.report('reconnecting')
    this.retry = this.setTimer(() => {
      this.retry = null
      this.socket = this.dial(false)
    }, this.backoffMs())
    this.attempts += 1
  }

  /** 500ms, then double each time, up to 8s however long the backend is away. */
  private backoffMs(): number {
    return Math.min(RECONNECT_BASE_MS * 2 ** this.attempts, RECONNECT_CAP_MS)
  }

  private cancel(): void {
    this.cancelSlowOpen()
    if (this.retry !== null) this.clearTimer(this.retry)
    this.retry = null
  }

  private cancelSlowOpen(): void {
    if (this.slowOpen !== null) this.clearTimer(this.slowOpen)
    this.slowOpen = null
  }

  private report(status: ConnectionStatus): void {
    if (this.state === status) return
    this.state = status
    for (const watcher of [...this.watchers]) watcher(status)
  }
}
