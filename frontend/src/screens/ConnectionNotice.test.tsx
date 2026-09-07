import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import { ConnectionNotice } from './ConnectionNotice'

function notice(): string | null {
  return screen.queryByRole('status')?.textContent ?? null
}

describe('ConnectionNotice', () => {
  it('says nothing while the connection is behaving', () => {
    render(<ConnectionNotice status="open" probing={false} />)

    expect(notice()).toBeNull()
  })

  it('says nothing while the first socket is still opening promptly', () => {
    render(<ConnectionNotice status="connecting" probing={false} />)

    expect(notice()).toBeNull()
  })

  it('says it is reconnecting while the socket is down', () => {
    render(<ConnectionNotice status="reconnecting" probing={false} />)

    expect(notice()).toBe('Reconnecting…')
  })

  it('says the server is waking up when the socket is slow to open', () => {
    render(<ConnectionNotice status="waking" probing={false} />)

    expect(notice()).toBe('Waking up the server')
  })

  it('says the server is waking up when the health request is the slow one', () => {
    render(<ConnectionNotice status="connecting" probing />)

    expect(notice()).toBe('Waking up the server')
  })

  it('puts the dropped socket first when the server is slow as well', () => {
    render(<ConnectionNotice status="reconnecting" probing />)

    expect(notice()).toBe('Reconnecting…')
  })
})
