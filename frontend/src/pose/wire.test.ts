import { describe, expect, it } from 'vitest'

import { toWireFrame } from './wire'
import type { PoseLandmark } from './wire'

/** 33 landmarks whose x rises with the index, so a reordering or flip would show. */
function frameLandmarks(): PoseLandmark[] {
  return Array.from({ length: 33 }, (_unused, index) => ({
    x: index / 100,
    y: 0.5,
    z: -0.1,
    visibility: 0.8,
  }))
}

describe('toWireFrame', () => {
  it('carries the timestamp and all 33 landmarks as four-number tuples', () => {
    const frame = toWireFrame(frameLandmarks(), 1234)

    expect(frame.t).toBe(1234)
    expect(frame.lm).toHaveLength(33)
    expect(frame.lm[0]).toEqual([0, 0.5, -0.1, 0.8])
    for (const landmark of frame.lm) {
      expect(landmark).toHaveLength(4)
    }
  })

  it('leaves x in image space, because only the preview is mirrored (ADR-0006)', () => {
    const landmarks = frameLandmarks()
    landmarks[15] = { x: 0.25, y: 0.4, z: 0, visibility: 0.9 }

    const frame = toWireFrame(landmarks, 0)

    expect(frame.lm[15][0]).toBe(0.25)
  })

  it('reports a landmark with no visibility score as invisible', () => {
    const landmarks = frameLandmarks()
    landmarks[0] = { x: 0.1, y: 0.2, z: 0.3 }

    expect(toWireFrame(landmarks, 0).lm[0]).toEqual([0.1, 0.2, 0.3, 0])
  })

  it('rejects a reading that is not a full set of 33 landmarks', () => {
    expect(() => toWireFrame(frameLandmarks().slice(0, 20), 0)).toThrow(/33/)
  })
})
