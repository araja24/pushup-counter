import { describe, expect, it } from 'vitest'

import { MUTE_KEY, loadMuted, saveMuted } from './mute'
import type { Preferences } from './mute'

function memoryStorage(initial: Record<string, string> = {}): Preferences {
  const values = new Map(Object.entries(initial))
  return {
    getItem: (key) => values.get(key) ?? null,
    setItem: (key, value) => {
      values.set(key, value)
    },
  }
}

describe('the mute preference', () => {
  it('round-trips through storage so the choice survives the next set', () => {
    const storage = memoryStorage()

    saveMuted(true, storage)

    expect(loadMuted(storage)).toBe(true)
  })

  it('plays tones for a user who has never touched the toggle', () => {
    expect(loadMuted(memoryStorage())).toBe(false)
  })

  it('can be turned back on again', () => {
    const storage = memoryStorage({ [MUTE_KEY]: 'true' })

    saveMuted(false, storage)

    expect(loadMuted(storage)).toBe(false)
  })

  it('keeps tones on when storage is refused rather than failing the set', () => {
    const refused: Preferences = {
      getItem: () => {
        throw new Error('storage is disabled')
      },
      setItem: () => {
        throw new Error('storage is disabled')
      },
    }

    expect(() => saveMuted(true, refused)).not.toThrow()
    expect(loadMuted(refused)).toBe(false)
  })
})
