import { render } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { PositioningScreen } from './PositioningScreen'
import type { LandmarkSocket } from '../net/socket'
import type { WireFrame } from '../pose/wire'

const landmarks = Array.from({ length: 33 }, () => ({ x: 0.5, y: 0.5, z: 0, visibility: 0.9 }))

// Stands in for the landmarker, handing the screen one complete detection.
vi.mock('../camera/usePoseTracking', () => ({
  usePoseTracking: (
    _video: unknown,
    _canvas: unknown,
    onLandmarks?: (found: typeof landmarks, t: number) => void,
  ) => {
    onLandmarks?.(landmarks, 1234.6)
    return { phase: 'tracking', error: null, delegate: 'GPU', guard: { ready: true, missing: [] } }
  },
}))

describe('PositioningScreen', () => {
  it('streams frames from the moment the connection opens, before any set', () => {
    const sent: WireFrame[] = []
    const socket = {
      listen: () => () => {},
      sendFrame: (frame: WireFrame) => {
        sent.push(frame)
        return 'sent' as const
      },
      start: vi.fn(),
      stop: vi.fn(),
      reset: vi.fn(),
    } satisfies LandmarkSocket

    render(
      <PositioningScreen stream={{} as MediaStream} socket={socket} onStart={vi.fn()} />,
    )

    expect(sent).toHaveLength(1)
    expect(sent[0].lm).toHaveLength(33)
    expect(sent[0].t).toBe(1235)
    expect(socket.start).not.toHaveBeenCalled()
  })
})
