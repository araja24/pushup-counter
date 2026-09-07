import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'

import App from './App'

describe('App', () => {
  it('names the app so a visitor knows what they opened', () => {
    render(<App />)

    expect(screen.getByRole('heading', { name: 'PushForm' })).toBeInTheDocument()
  })
})
