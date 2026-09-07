import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { WAKING_MS, probeHealth } from './wakeup'

/** A fetch the test settles by hand. */
function pendingFetch() {
  let settle: (response: { ok: boolean }) => void = () => {}
  let fail: (cause: Error) => void = () => {}
  const fetchFn = vi.fn(
    () =>
      new Promise<Response>((resolve, reject) => {
        settle = (response) => resolve(response as Response)
        fail = reject
      }),
  )
  return { fetchFn, answer: () => settle({ ok: true }), refuse: () => fail(new Error('offline')) }
}

beforeEach(() => {
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
})

describe('probeHealth', () => {
  it('says the server is waking up once the probe outlasts the delay', async () => {
    const { fetchFn, answer } = pendingFetch()
    const waking: boolean[] = []
    const probe = probeHealth('/api/health', { fetchFn, onWaking: (state) => waking.push(state) })

    vi.advanceTimersByTime(WAKING_MS - 1)
    expect(waking).toEqual([])

    vi.advanceTimersByTime(1)
    expect(waking).toEqual([true])

    answer()
    await expect(probe).resolves.toBe(true)
    // The notice comes down the moment the server answers.
    expect(waking).toEqual([true, false])
  })

  it('never mentions waking up when the server answers promptly', async () => {
    const { fetchFn, answer } = pendingFetch()
    const waking: boolean[] = []
    const probe = probeHealth('/api/health', { fetchFn, onWaking: (state) => waking.push(state) })

    answer()
    await probe
    vi.advanceTimersByTime(WAKING_MS * 4)

    expect(waking).toEqual([false])
  })

  it('clears the notice when the probe fails, rather than leaving it on screen', async () => {
    const { fetchFn, refuse } = pendingFetch()
    const waking: boolean[] = []
    const probe = probeHealth('/api/health', { fetchFn, onWaking: (state) => waking.push(state) })

    vi.advanceTimersByTime(WAKING_MS)
    refuse()

    await expect(probe).resolves.toBe(false)
    expect(waking).toEqual([true, false])
  })

  it('asks the backend it was pointed at, once', async () => {
    const { fetchFn, answer } = pendingFetch()
    const probe = probeHealth('https://pushform.example/api/health', { fetchFn, onWaking: () => {} })

    answer()
    await probe

    expect(fetchFn).toHaveBeenCalledTimes(1)
    expect(fetchFn).toHaveBeenCalledWith('https://pushform.example/api/health')
  })

  it('the delay is a second and a half', () => {
    expect(WAKING_MS).toBe(1500)
  })
})
