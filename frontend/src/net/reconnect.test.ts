import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import {
  RECONNECT_BASE_MS,
  RECONNECT_CAP_MS,
  ReconnectingSocket,
  WAKING_MS,
} from './reconnect'
import type { ConnectionStatus, ServerMessage } from './socket'
import type { WireFrame } from '../pose/wire'

/** A WebSocket the test opens, drops and reads back. */
class FakeWebSocket {
  readyState = 0
  bufferedAmount = 0
  sent: string[] = []
  onopen: (() => void) | null = null
  onclose: (() => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null

  send(data: string): void {
    this.sent.push(data)
  }

  close(): void {
    this.readyState = 3
  }

  /** The handshake finished. */
  accept(): void {
    this.readyState = 1
    this.onopen?.()
  }

  /** The wire broke, or the backend went away. */
  drop(): void {
    this.readyState = 3
    this.onclose?.()
  }

  deliver(message: object): void {
    this.onmessage?.({ data: JSON.stringify(message) } as MessageEvent)
  }

  commands(): { cmd: string; set_id?: string }[] {
    return this.sent
      .map((text) => JSON.parse(text) as { cmd?: string })
      .filter((sent): sent is { cmd: string } => 'cmd' in sent)
  }
}

function frame(t: number): WireFrame {
  return { t, lm: Array.from({ length: 33 }, () => [0.5, 0.5, 0, 0.9]) }
}

/** A ReconnectingSocket over fakes, with every timer the test's to wind on. */
function connect() {
  const sockets: FakeWebSocket[] = []
  const statuses: ConnectionStatus[] = []
  const socket = new ReconnectingSocket('ws://phone/ws', {
    open: () => {
      const fake = new FakeWebSocket()
      sockets.push(fake)
      return fake as unknown as WebSocket
    },
    now: () => sockets.length * 1000,
    setTimer: (run, ms) => setTimeout(run, ms),
    clearTimer: (handle) => clearTimeout(handle),
  })
  socket.listenStatus((status) => statuses.push(status))
  const latest = () => sockets[sockets.length - 1]
  return { socket, sockets, statuses, latest }
}

beforeEach(() => {
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
})

describe('ReconnectingSocket', () => {
  it('waits longer before each attempt, doubling up to the cap', () => {
    const { sockets, latest } = connect()
    latest().accept()

    for (const delay of [500, 1000, 2000, 4000, 8000, 8000]) {
      const dialled = sockets.length
      latest().drop()
      vi.advanceTimersByTime(delay - 1)
      expect(sockets).toHaveLength(dialled)
      vi.advanceTimersByTime(1)
      expect(sockets).toHaveLength(dialled + 1)
    }

    expect(RECONNECT_BASE_MS).toBe(500)
    expect(RECONNECT_CAP_MS).toBe(8000)
  })

  it('starts from the first delay again once a socket has opened', () => {
    const { sockets, latest } = connect()
    latest().accept()

    latest().drop()
    vi.advanceTimersByTime(RECONNECT_BASE_MS)
    latest().accept()
    latest().drop()
    vi.advanceTimersByTime(RECONNECT_BASE_MS)

    // Three sockets: the original, the first retry, and this one 500ms after it dropped.
    expect(sockets).toHaveLength(3)
  })

  it('resumes the set in progress as the first thing it says on the new socket', () => {
    const { socket, latest } = connect()
    latest().accept()
    socket.start('set-1')

    latest().drop()
    vi.advanceTimersByTime(RECONNECT_BASE_MS)
    latest().accept()

    expect(latest().commands()[0]).toEqual({ cmd: 'resume', set_id: 'set-1' })
  })

  it('asks to resume nothing when no set was running', () => {
    const { latest } = connect()
    latest().accept()

    latest().drop()
    vi.advanceTimersByTime(RECONNECT_BASE_MS)
    latest().accept()

    expect(latest().commands()).toEqual([])
  })

  it('does not resume a set the user has already stopped', () => {
    const { socket, latest } = connect()
    latest().accept()
    socket.start('set-1')
    socket.stop()

    latest().drop()
    vi.advanceTimersByTime(RECONNECT_BASE_MS)
    latest().accept()

    expect(latest().commands()).toEqual([])
  })

  it('resumes the newest set after a reset, never the abandoned one', () => {
    const { socket, latest } = connect()
    latest().accept()
    socket.start('set-1')
    socket.reset()
    socket.start('set-2')

    latest().drop()
    vi.advanceTimersByTime(RECONNECT_BASE_MS)
    latest().accept()

    expect(latest().commands()[0]).toEqual({ cmd: 'resume', set_id: 'set-2' })
  })

  it('says it is reconnecting while it is down, and open once it is back', () => {
    const { socket, statuses, latest } = connect()
    latest().accept()

    latest().drop()
    expect(socket.status).toBe('reconnecting')

    vi.advanceTimersByTime(RECONNECT_BASE_MS)
    latest().accept()

    expect(socket.status).toBe('open')
    expect(statuses).toEqual(['open', 'reconnecting', 'open'])
  })

  it('says the server is waking up when the first socket is slow to open', () => {
    const { socket, latest } = connect()

    vi.advanceTimersByTime(WAKING_MS)
    expect(socket.status).toBe('waking')

    latest().accept()
    expect(socket.status).toBe('open')
  })

  it('never says waking up when the socket opens promptly', () => {
    const { socket, statuses, latest } = connect()

    latest().accept()
    vi.advanceTimersByTime(WAKING_MS * 4)

    expect(statuses).toEqual(['open'])
    expect(socket.status).toBe('open')
  })

  it('keeps every listener across a reconnect, so the screen never goes deaf', () => {
    const { socket, latest } = connect()
    latest().accept()
    const heard: ServerMessage[] = []
    socket.listen((message) => heard.push(message))

    latest().drop()
    vi.advanceTimersByTime(RECONNECT_BASE_MS)
    latest().accept()
    latest().deliver({ type: 'state', reps: 3 })

    expect(heard).toEqual([{ type: 'state', reps: 3 }])
  })

  it('sends frames down whichever socket is up, and none while it is down', () => {
    const { socket, latest } = connect()
    latest().accept()

    expect(socket.sendFrame(frame(1))).toBe('sent')
    latest().drop()
    expect(socket.sendFrame(frame(2))).toBe('closed')

    vi.advanceTimersByTime(RECONNECT_BASE_MS)
    latest().accept()
    expect(socket.sendFrame(frame(3))).toBe('sent')
  })

  it('stays shut once the page closes it', () => {
    const { socket, sockets, latest } = connect()
    latest().accept()

    socket.close()
    latest().drop()
    vi.advanceTimersByTime(RECONNECT_CAP_MS * 2)

    expect(sockets).toHaveLength(1)
    expect(socket.status).toBe('closed')
  })
})
