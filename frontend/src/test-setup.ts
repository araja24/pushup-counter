import '@testing-library/jest-dom/vitest'

import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

// `globals: false`, so Testing Library's own auto-cleanup never registers.
afterEach(cleanup)

// jsdom has no media pipeline: play() would log "Not implemented" for every
// screen that shows the camera preview.
Object.defineProperty(HTMLMediaElement.prototype, 'play', {
  writable: true,
  value: () => Promise.resolve(),
})
