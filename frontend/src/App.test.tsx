import { render, screen } from '@testing-library/react'
import { act } from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import App from './App'
import { WAKING_MS } from './net/wakeup'

/** A health check the test answers when it chooses. */
function pendingHealth() {
  let answer: () => void = () => {}
  const fetchFn = vi.fn(
    () =>
      new Promise<Response>((resolve) => {
        answer = () => resolve({ ok: true } as Response)
      }),
  )
  vi.stubGlobal('fetch', fetchFn)
  return { answer: async () => await act(async () => answer()) }
}

beforeEach(() => {
  vi.useFakeTimers()
})

afterEach(() => {
  vi.useRealTimers()
  vi.unstubAllGlobals()
})

describe('App', () => {
  it('names the app so a visitor knows what they opened', () => {
    pendingHealth()

    render(<App />)

    expect(screen.getByRole('heading', { name: 'PushForm' })).toBeInTheDocument()
  })

  it('says the server is waking up when the first health check drags on', async () => {
    const { answer } = pendingHealth()
    render(<App />)

    act(() => vi.advanceTimersByTime(WAKING_MS - 1))
    expect(screen.queryByText('Waking up the server')).not.toBeInTheDocument()

    act(() => vi.advanceTimersByTime(1))
    expect(screen.getByRole('status')).toHaveTextContent('Waking up the server')

    await answer()
    expect(screen.queryByText('Waking up the server')).not.toBeInTheDocument()
  })
})
