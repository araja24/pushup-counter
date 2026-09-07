import { describe, expect, it, vi } from 'vitest'

import { BUFFER_LIMIT, FrameSocket } from './socket'
import type { ServerMessage } from './socket'
import type { WireFrame } from '../pose/wire'

/** A WebSocket that records what was sent and lets a test set the pressure. */
class FakeWebSocket {
  static readonly CONNECTING = 0
  static readonly OPEN = 1
  readyState: number = FakeWebSocket.OPEN
  bufferedAmount = 0
  sent: string[] = []
  closed = false
  onopen: (() => void) | null = null
  onmessage: ((event: MessageEvent) => void) | null = null

  send(data: string): void {
    this.sent.push(data)
  }

  close(): void {
    this.closed = true
  }

  /** Pretend the backend said something. */
  deliver(message: object): void {
    this.onmessage?.({ data: JSON.stringify(message) } as MessageEvent)
  }

  frames(): WireFrame[] {
    return this.sent.map((text) => JSON.parse(text) as WireFrame).filter((sent) => 'lm' in sent)
  }

  commands(): { cmd: string; set_id?: string }[] {
    return this.sent
      .map((text) => JSON.parse(text) as { cmd?: string })
      .filter((sent): sent is { cmd: string } => 'cmd' in sent)
  }
}

function frameAt(t: number): WireFrame {
  return { t, lm: Array.from({ length: 33 }, () => [0.5, 0.5, 0, 0.9]) }
}

/** A FrameSocket over a fake, with a clock the test winds on itself. */
function connect() {
  const fake = new FakeWebSocket()
  const clock = { ms: 0 }
  const socket = new FrameSocket('ws://phone/ws', {
    open: () => fake as unknown as WebSocket,
    now: () => clock.ms,
  })
  return { fake, clock, socket }
}

describe('FrameSocket', () => {
  it('drops frames rather than queueing them when the connection is backed up', () => {
    const { fake, clock, socket } = connect()
    clock.ms = 1000
    expect(socket.sendFrame(frameAt(1))).toBe('sent')

    fake.bufferedAmount = BUFFER_LIMIT + 1
    clock.ms = 2000
    const backedUp = socket.sendFrame(frameAt(2))
    clock.ms = 3000
    socket.sendFrame(frameAt(3))

    expect(backedUp).toBe('dropped')
    expect(socket.dropped).toBe(2)
    expect(fake.frames().map((frame) => frame.t)).toEqual([1])
  })

  it('sends again once the backlog has cleared, with no stale frames behind it', () => {
    const { fake, clock, socket } = connect()
    fake.bufferedAmount = BUFFER_LIMIT + 1
    socket.sendFrame(frameAt(1))

    fake.bufferedAmount = 0
    clock.ms = 1000
    socket.sendFrame(frameAt(2))

    expect(fake.frames().map((frame) => frame.t)).toEqual([2])
  })

  it('holds frames to thirty a second, however fast the camera runs', () => {
    const { fake, clock, socket } = connect()

    const results = [0, 5, 10, 34, 40, 68].map((ms) => {
      clock.ms = ms
      return socket.sendFrame(frameAt(ms))
    })

    expect(results).toEqual(['sent', 'throttled', 'throttled', 'sent', 'throttled', 'sent'])
    expect(fake.frames()).toHaveLength(3)
  })

  it('never sends a frame down a socket that is not open', () => {
    const { fake, socket } = connect()
    fake.readyState = FakeWebSocket.CONNECTING

    expect(socket.sendFrame(frameAt(1))).toBe('closed')
    expect(fake.sent).toEqual([])
  })

  it('starts a set with the id the caller chose', () => {
    const { fake, socket } = connect()

    socket.start('set-1')
    socket.stop()
    socket.reset()

    expect(fake.commands()).toEqual([
      { cmd: 'start', set_id: 'set-1' },
      { cmd: 'stop' },
      { cmd: 'reset' },
    ])
  })

  it('holds a command until the socket opens, so an early start is not lost', () => {
    const { fake, socket } = connect()
    fake.readyState = FakeWebSocket.CONNECTING

    socket.start('set-1')
    expect(fake.sent).toEqual([])

    fake.readyState = FakeWebSocket.OPEN
    fake.onopen?.()

    expect(fake.commands()).toEqual([{ cmd: 'start', set_id: 'set-1' }])
  })

  it('hands every server message to the listeners', () => {
    const { fake, socket } = connect()
    const heard: ServerMessage[] = []
    const stop = socket.listen((message) => heard.push(message))

    fake.deliver({ type: 'rep', index: 1, counted: true })
    stop()
    fake.deliver({ type: 'rep', index: 2, counted: true })

    expect(heard).toEqual([{ type: 'rep', index: 1, counted: true }])
  })

  it('ignores a message that is not JSON rather than tearing the connection down', () => {
    const { fake, socket } = connect()
    const listener = vi.fn()
    socket.listen(listener)

    fake.onmessage?.({ data: 'not json' } as MessageEvent)

    expect(listener).not.toHaveBeenCalled()
  })
})
