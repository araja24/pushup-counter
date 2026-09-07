import '@testing-library/jest-dom/vitest'

import { cleanup } from '@testing-library/react'
import { afterEach } from 'vitest'

// `globals: false`, so Testing Library's own auto-cleanup never registers.
afterEach(cleanup)
