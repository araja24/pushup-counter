/**
 * Knocking on a backend that may be asleep.
 *
 * The backend sleeps when nobody has used it for a while (docs/adr/0007), and
 * the first request of the day pays for the wake-up. A user staring at a screen
 * that does nothing assumes the app is broken, so anything that outlasts a short
 * wait says so instead.
 */

/** How long the phone waits before admitting the server is still waking up. */
export const WAKING_MS = 1500

/** A timer the caller can replace, so tests never wait in real time. */
export type TimerHandle = ReturnType<typeof setTimeout>

export interface ProbeOptions {
  /** Told `true` when the wait passes the delay, and `false` when it is over. */
  onWaking: (waking: boolean) => void
  fetchFn?: (url: string) => Promise<Response>
  setTimer?: (run: () => void, ms: number) => TimerHandle
  clearTimer?: (handle: TimerHandle) => void
  delayMs?: number
}

/**
 * Ask the backend for a heartbeat, reporting a long wait as "waking up".
 *
 * Returns whether the backend answered. A refusal is an answer too: the notice
 * comes down either way rather than being left on screen forever.
 */
export async function probeHealth(url: string, options: ProbeOptions): Promise<boolean> {
  const {
    onWaking,
    fetchFn = (target: string) => fetch(target),
    setTimer = (run: () => void, ms: number) => setTimeout(run, ms),
    clearTimer = (handle: TimerHandle) => clearTimeout(handle),
    delayMs = WAKING_MS,
  } = options

  const slow = setTimer(() => onWaking(true), delayMs)
  try {
    const response = await fetchFn(url)
    return response.ok
  } catch {
    return false
  } finally {
    clearTimer(slow)
    onWaking(false)
  }
}
