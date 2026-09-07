import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { SummaryScreen } from './SummaryScreen'
import type { SummaryMessage } from '../net/socket'

const summary: SummaryMessage = {
  type: 'summary',
  reps: 5,
  rejected: 1,
  faults: { partial_rom: 1, hip_sag: 0, hip_pike: 0 },
  duration_ms: 12400,
  avg_rep_ms: 1500,
}

describe('SummaryScreen', () => {
  it('shows what the set came to, in seconds rather than milliseconds', () => {
    render(<SummaryScreen summary={summary} onAnother={vi.fn()} />)

    expect(screen.getByText('5')).toBeInTheDocument()
    expect(screen.getByText('reps counted')).toBeInTheDocument()
    expect(screen.getByText('12.4 s')).toBeInTheDocument()
    expect(screen.getByText('1.5 s')).toBeInTheDocument()
    expect(screen.getByText('1')).toBeInTheDocument()
  })

  it('offers another set on the connection that is already open', () => {
    const onAnother = vi.fn()
    render(<SummaryScreen summary={summary} onAnother={onAnother} />)

    fireEvent.click(screen.getByRole('button', { name: 'Another set' }))

    expect(onAnother).toHaveBeenCalled()
  })
})
