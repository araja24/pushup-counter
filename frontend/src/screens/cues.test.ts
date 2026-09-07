import { describe, expect, it } from 'vitest'

import { CANT_SEE_YOU, LOCK_OUT, cueFor } from './cues'
import type { StateMessage } from '../net/socket'

function state(overrides: Partial<StateMessage> = {}): StateMessage {
  return {
    type: 'state',
    reps: 0,
    rejected: 0,
    phase: 'UP',
    elbow_angle: 168,
    hip_angle: 179,
    aligned: true,
    tracking: true,
    stalled: false,
    side: 'left',
    ...overrides,
  }
}

describe('cueFor', () => {
  it('says nothing while the backend is counting normally', () => {
    expect(cueFor(state())).toBeNull()
  })

  it('asks the user to come back into shot when Tracking is Lost', () => {
    expect(cueFor(state({ tracking: false }))).toBe(CANT_SEE_YOU)
  })

  it('asks for a lockout on a Stall', () => {
    expect(cueFor(state({ stalled: true }))).toBe(LOCK_OUT)
  })

  it('asks the user to come back into shot first when both are true', () => {
    // A Stall the camera cannot see is not worth prompting about: nothing the
    // user does about their elbows helps until they are in shot again.
    expect(cueFor(state({ tracking: false, stalled: true }))).toBe(CANT_SEE_YOU)
  })

  it('is words, not a colour', () => {
    expect(CANT_SEE_YOU).toMatch(/\w/)
    expect(LOCK_OUT).toMatch(/\w/)
  })
})
