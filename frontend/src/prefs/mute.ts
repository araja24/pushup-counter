/**
 * Whether the rep tones are muted, remembered between visits.
 *
 * Tones are on by default: a user who has never touched the toggle is training
 * with the phone propped up and out of reach, and the tone is the only feedback
 * they get without looking.
 */

export const MUTE_KEY = 'pushform.muted'

/** Just enough of `Storage` to remember one flag. */
export interface Preferences {
  getItem(key: string): string | null
  setItem(key: string, value: string): void
}

export function loadMuted(storage: Preferences | null = browserStorage()): boolean {
  try {
    return storage?.getItem(MUTE_KEY) === 'true'
  } catch {
    // Storage can be refused outright (private browsing); tones stay on.
    return false
  }
}

export function saveMuted(muted: boolean, storage: Preferences | null = browserStorage()): void {
  try {
    storage?.setItem(MUTE_KEY, String(muted))
  } catch {
    // A preference that cannot be saved is not worth failing a set over.
  }
}

function browserStorage(): Preferences | null {
  try {
    return globalThis.localStorage ?? null
  } catch {
    return null
  }
}
