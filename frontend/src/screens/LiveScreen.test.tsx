import { fireEvent, render, screen } from '@testing-library/react'
import { act } from 'react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { LiveScreen } from './LiveScreen'
import { MUTE_KEY } from '../prefs/mute'
import type { LandmarkSocket, ServerMessage } from '../net/socket'

const playHighTone = vi.hoisted(() => vi.fn())
vi.mock('../audio/tones', () => ({ playHighTone }))
// The landmarker needs a camera and a GPU; the Connection is what is under test.
vi.mock('../camera/usePoseTracking', () => ({
  usePoseTracking: () => ({ phase: 'tracking', error: null, delegate: 'GPU', guard: { ready: true, missing: [] } }),
}))

/** A Connection the test speaks for. */
function fakeSocket() {
  const listeners: ((message: ServerMessage) => void)[] = []
  const commands: string[] = []
  const socket: LandmarkSocket = {
    listen: (listener) => {
      listeners.push(listener)
      return () => listeners.splice(listeners.indexOf(listener), 1)
    },
    sendFrame: () => 'sent',
    start: (setId) => commands.push(`start:${setId}`),
    stop: () => commands.push('stop'),
    reset: () => commands.push('reset'),
  }
  const say = (message: ServerMessage) => {
    act(() => {
      for (const listener of [...listeners]) listener(message)
    })
  }
  return { socket, commands, say }
}

function state(overrides: Partial<Extract<ServerMessage, { type: 'state' }>> = {}) {
  return {
    type: 'state',
    reps: 0,
    rejected: 0,
    phase: 'UP',
    elbow_angle: 168.4,
    hip_angle: 179,
    aligned: null,
    tracking: true,
    stalled: false,
    side: 'left',
    ...overrides,
  } as ServerMessage
}

function rep(counted: boolean, index = 1) {
  return {
    type: 'rep',
    index,
    counted,
    label: 'unlabelled',
    reason: null,
    source: 'none',
    min_elbow: 72,
    max_elbow: 171,
    duration_ms: 900,
    confidence: null,
  } as ServerMessage
}

function renderLive(onFinished = vi.fn()) {
  const { socket, commands, say } = fakeSocket()
  render(
    <LiveScreen stream={{} as MediaStream} socket={socket} onFinished={onFinished} />,
  )
  return { commands, say, onFinished }
}

beforeEach(() => {
  localStorage.clear()
  playHighTone.mockClear()
})

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('LiveScreen', () => {
  it('starts a set of its own as soon as it opens', () => {
    const { commands } = renderLive()

    expect(commands).toHaveLength(1)
    expect(commands[0]).toMatch(/^start:.+/)
  })

  it('shows the count the backend reports, and announces it to a screen reader', () => {
    const { say } = renderLive()

    say(state({ reps: 5 }))

    expect(screen.getByText('5')).toBeInTheDocument()
    expect(screen.getByText('5 reps')).toHaveAttribute('aria-live', 'polite')
  })

  it('shows the phase and elbow angle so the user can see what the backend sees', () => {
    const { say } = renderLive()

    say(state({ phase: 'DOWN', elbow_angle: 82.3 }))

    expect(screen.getByText('DOWN 82°')).toBeInTheDocument()
  })

  it('keeps a tally of rejected reps beside the count', () => {
    const { say } = renderLive()

    say(state({ reps: 4, rejected: 2 }))

    expect(screen.getByText('2 rejected')).toBeInTheDocument()
  })

  it('sounds a tone and buzzes the phone on a counted rep', () => {
    const vibrate = vi.fn()
    vi.stubGlobal('navigator', { ...navigator, vibrate })
    const { say } = renderLive()

    say(rep(true))

    expect(playHighTone).toHaveBeenCalledTimes(1)
    expect(vibrate).toHaveBeenCalledWith(50)
  })

  it('says nothing for a rejected rep', () => {
    const { say } = renderLive()

    say(rep(false))

    expect(playHighTone).not.toHaveBeenCalled()
  })

  it('stays silent while muted, and remembers the choice for the next set', () => {
    const { say } = renderLive()

    fireEvent.click(screen.getByRole('button', { name: 'Mute' }))
    say(rep(true))

    expect(playHighTone).not.toHaveBeenCalled()
    expect(localStorage.getItem(MUTE_KEY)).toBe('true')
    expect(screen.getByRole('button', { name: 'Unmute' })).toHaveAttribute(
      'aria-pressed',
      'true',
    )
  })

  it('opens muted when the user muted a previous set', () => {
    localStorage.setItem(MUTE_KEY, 'true')

    renderLive()

    expect(screen.getByRole('button', { name: 'Unmute' })).toBeInTheDocument()
  })

  it('stops the set on Stop and hands the summary on when it arrives', () => {
    const { commands, say, onFinished } = renderLive()

    fireEvent.click(screen.getByRole('button', { name: 'Stop' }))
    const summary = {
      type: 'summary',
      reps: 5,
      rejected: 0,
      faults: { partial_rom: 0, hip_sag: 0, hip_pike: 0 },
      duration_ms: 12000,
      avg_rep_ms: 1500,
    } as ServerMessage

    say(summary)

    expect(commands).toContain('stop')
    expect(onFinished).toHaveBeenCalledWith(summary)
  })

  it('throws the set away on Reset without ending it', () => {
    const { commands, onFinished } = renderLive()

    fireEvent.click(screen.getByRole('button', { name: 'Reset' }))

    expect(commands).toContain('reset')
    expect(commands).not.toContain('stop')
    expect(onFinished).not.toHaveBeenCalled()
  })
})
