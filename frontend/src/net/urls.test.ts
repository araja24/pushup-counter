import { describe, expect, it } from 'vitest'

import { apiBaseUrl, frameSocketUrl } from './urls'

describe('apiBaseUrl', () => {
  it('serves the API from the same origin as the page', () => {
    const location = { protocol: 'https:', host: 'pushform.onrender.com' }

    expect(apiBaseUrl(location).http).toBe('https://pushform.onrender.com')
  })

  it('uses a secure WebSocket when the page is served over https', () => {
    const location = { protocol: 'https:', host: 'pushform.onrender.com' }

    expect(apiBaseUrl(location).ws).toBe('wss://pushform.onrender.com')
  })

  it('uses a plain WebSocket when the page is served over http', () => {
    const location = { protocol: 'http:', host: 'localhost:5173' }

    expect(apiBaseUrl(location)).toEqual({
      http: 'http://localhost:5173',
      ws: 'ws://localhost:5173',
    })
  })

  it('keeps a non-default port so a phone on the LAN reaches the dev server', () => {
    const location = { protocol: 'http:', host: '192.168.1.20:8000' }

    expect(apiBaseUrl(location).ws).toBe('ws://192.168.1.20:8000')
  })
})

describe('frameSocketUrl', () => {
  it('is a secure socket on a page served over https', () => {
    expect(frameSocketUrl({ protocol: 'https:', host: 'pushform.onrender.com' })).toBe(
      'wss://pushform.onrender.com/ws',
    )
  })

  it('is a plain socket on the http dev server', () => {
    expect(frameSocketUrl({ protocol: 'http:', host: 'localhost:5173' })).toBe(
      'ws://localhost:5173/ws',
    )
  })
})
