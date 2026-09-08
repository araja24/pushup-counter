import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { PositioningScreen } from './PositioningScreen'
import type { LandmarkSocket } from '../net/socket'
import type { WireFrame } from '../pose/wire'

const landmarks = Array.from({ length: 33 }, () => ({ x: 0.5, y: 0.5, z: 0, visibility: 0.9 }))

const tracking = vi.hoisted(() => ({
  result: {
    phase: 'tracking' as string,
    error: null as string | null,
    delegate: 'GPU' as string | null,
    guard: { ready: true, missing: [] as string[] },
  },
}))

// Stands in for the landmarker, handing the screen one complete detection.
vi.mock('../camera/usePoseTracking', () => ({
  usePoseTracking: (
    _video: unknown,
    _canvas: unknown,
    onLandmarks?: (found: typeof landmarks, t: number) => void,
  ) => {
    onLandmarks?.(landmarks, 1234.6)
    return tracking.result
  },
}))

function dummySocket(): LandmarkSocket {
  return {
    listen: () => () => {},
    sendFrame: () => 'sent',
    start: vi.fn(),
    stop: vi.fn(),
    reset: vi.fn(),
  }
}

beforeEach(() => {
  tracking.result = {
    phase: 'tracking',
    error: null,
    delegate: 'GPU',
    guard: { ready: true, missing: [] },
  }
})

describe('PositioningScreen', () => {
  it('streams frames from the moment the connection opens, before any set', () => {
    const sent: WireFrame[] = []
    const socket = {
      ...dummySocket(),
      sendFrame: (frame: WireFrame) => {
        sent.push(frame)
        return 'sent' as const
      },
    } satisfies LandmarkSocket

    render(
      <PositioningScreen stream={{} as MediaStream} socket={socket} onStart={vi.fn()} />,
    )

    expect(sent).toHaveLength(1)
    expect(sent[0].lm).toHaveLength(33)
    expect(sent[0].t).toBe(1235)
    expect(socket.start).not.toHaveBeenCalled()
  })

  it('lets the user press Start before the positioning guard is ready', () => {
    tracking.result = {
      phase: 'starting',
      error: null,
      delegate: null,
      guard: { ready: false, missing: [] },
    }
    const onStart = vi.fn()
    const stream = {} as MediaStream

    render(<PositioningScreen stream={stream} socket={dummySocket()} onStart={onStart} />)

    const start = screen.getByRole('button', { name: 'Start' })
    expect(start).toBeEnabled()
    fireEvent.click(start)
    expect(onStart).toHaveBeenCalledWith(stream)
  })

  it('disables Start when pose tracking has failed', () => {
    tracking.result = {
      phase: 'failed',
      error: 'The pose model could not be loaded',
      delegate: null,
      guard: { ready: false, missing: [] },
    }

    render(
      <PositioningScreen stream={{} as MediaStream} socket={dummySocket()} onStart={vi.fn()} />,
    )

    expect(screen.getByRole('button', { name: 'Start' })).toBeDisabled()
  })
})
