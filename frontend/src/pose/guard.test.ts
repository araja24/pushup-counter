import { describe, expect, it } from 'vitest'

import { LANDMARK, VISIBILITY_FLOOR, positioningGuard } from './guard'

/** Visibilities for a body fully in frame, which any test can then take away from. */
function allVisible(): number[] {
  return Array.from({ length: 33 }, () => 0.9)
}

describe('positioningGuard', () => {
  it('is ready and lists nothing missing when the whole body is in frame', () => {
    expect(positioningGuard(allVisible())).toEqual({ ready: true, missing: [] })
  })

  it('names a shoulder that has dropped below the floor', () => {
    const visibilities = allVisible()
    visibilities[LANDMARK.leftShoulder] = 0.2

    expect(positioningGuard(visibilities)).toEqual({
      ready: false,
      missing: ['left shoulder'],
    })
  })

  it('names every missing shoulder and hip in head-to-toe order', () => {
    const visibilities = allVisible()
    visibilities[LANDMARK.rightShoulder] = 0.1
    visibilities[LANDMARK.leftHip] = 0.1
    visibilities[LANDMARK.rightHip] = 0.1

    expect(positioningGuard(visibilities).missing).toEqual([
      'right shoulder',
      'left hip',
      'right hip',
    ])
  })

  it('is ready when only one arm is visible, because one side is enough', () => {
    const visibilities = allVisible()
    visibilities[LANDMARK.leftElbow] = 0.1
    visibilities[LANDMARK.leftWrist] = 0.1

    expect(positioningGuard(visibilities)).toEqual({ ready: true, missing: [] })
  })

  it('is not ready when the visible elbow and wrist are on opposite sides', () => {
    const visibilities = allVisible()
    visibilities[LANDMARK.leftWrist] = 0.1
    visibilities[LANDMARK.rightElbow] = 0.1

    expect(positioningGuard(visibilities)).toEqual({
      ready: false,
      missing: ['an elbow and a wrist on the same side'],
    })
  })

  it('asks for an elbow when neither elbow is visible', () => {
    const visibilities = allVisible()
    visibilities[LANDMARK.leftElbow] = 0.1
    visibilities[LANDMARK.rightElbow] = 0.1

    expect(positioningGuard(visibilities)).toEqual({
      ready: false,
      missing: ['an elbow'],
    })
  })

  it('asks for a wrist when neither wrist is visible', () => {
    const visibilities = allVisible()
    visibilities[LANDMARK.leftWrist] = 0.1
    visibilities[LANDMARK.rightWrist] = 0.1

    expect(positioningGuard(visibilities)).toEqual({
      ready: false,
      missing: ['a wrist'],
    })
  })

  it('asks for both when no arm landmark is visible at all', () => {
    const visibilities = allVisible()
    for (const index of [
      LANDMARK.leftElbow,
      LANDMARK.rightElbow,
      LANDMARK.leftWrist,
      LANDMARK.rightWrist,
    ]) {
      visibilities[index] = 0.1
    }

    expect(positioningGuard(visibilities).missing).toEqual(['an elbow', 'a wrist'])
  })

  it('treats a landmark sitting exactly on the visibility floor as visible', () => {
    const visibilities = allVisible()
    visibilities[LANDMARK.leftShoulder] = VISIBILITY_FLOOR

    expect(positioningGuard(visibilities).ready).toBe(true)
  })

  it('rejects a reading that is not a full set of 33 landmarks', () => {
    expect(() => positioningGuard([0.9, 0.9])).toThrow(/33/)
  })
})
