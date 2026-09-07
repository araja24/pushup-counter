import { describe, expect, it, vi } from 'vitest'

import { HIGH_TONE_HZ, TONE_MS, playHighTone } from './tones'

/** An AudioContext that records the note it was asked to play. */
function fakeContext(state = 'running') {
  const oscillator = {
    type: '',
    frequency: { value: 0 },
    connect: vi.fn(),
    start: vi.fn(),
    stop: vi.fn(),
  }
  const gain = {
    gain: { setValueAtTime: vi.fn(), exponentialRampToValueAtTime: vi.fn() },
    connect: vi.fn(),
  }
  const context = {
    state,
    currentTime: 2,
    destination: {},
    resume: vi.fn(),
    createOscillator: () => oscillator,
    createGain: () => gain,
  }
  return { context: context as unknown as AudioContext, oscillator, gain, resume: context.resume }
}

describe('playHighTone', () => {
  it('plays a short 880 Hz note so a counted rep is heard, not read', () => {
    const { context, oscillator } = fakeContext()

    playHighTone(context)

    expect(oscillator.frequency.value).toBe(HIGH_TONE_HZ)
    expect(oscillator.start).toHaveBeenCalledWith(2)
    expect(oscillator.stop).toHaveBeenCalledWith(2 + TONE_MS / 1000)
  })

  it('wakes an audio context the browser suspended until the first tap', () => {
    const { context, resume, oscillator } = fakeContext('suspended')

    playHighTone(context)

    expect(resume).toHaveBeenCalled()
    expect(oscillator.start).toHaveBeenCalled()
  })

  it('stays silent rather than throwing where the device has no audio', () => {
    expect(() => playHighTone(null)).not.toThrow()
  })
})
