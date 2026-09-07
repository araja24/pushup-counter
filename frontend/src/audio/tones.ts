/**
 * The sound a counted Rep makes.
 *
 * A short high tone, so the user knows the rep landed without looking at the
 * phone. It is synthesised rather than loaded: no asset to fetch, and it can be
 * played from inside the frame loop the moment a Rep arrives.
 */

/** The counted-Rep tone. The rejected-Rep tone is a lower one, and later work. */
export const HIGH_TONE_HZ = 880

export const TONE_MS = 120

const PEAK_GAIN = 0.2

let shared: AudioContext | null = null

/** Play the counted-Rep tone. Silent, never throwing, where audio is refused. */
export function playHighTone(context: AudioContext | null = sharedContext()): void {
  if (!context) return
  try {
    // A context created before the first tap starts suspended on mobile.
    if (context.state === 'suspended') void context.resume()
    playTone(context, HIGH_TONE_HZ, TONE_MS)
  } catch {
    // Audio is a nicety; a device that refuses it still counts reps.
  }
}

function playTone(context: AudioContext, hz: number, ms: number): void {
  const oscillator = context.createOscillator()
  const gain = context.createGain()
  const start = context.currentTime
  const end = start + ms / 1000

  oscillator.type = 'sine'
  oscillator.frequency.value = hz
  // Fade out, so the tone stops without a click.
  gain.gain.setValueAtTime(PEAK_GAIN, start)
  gain.gain.exponentialRampToValueAtTime(0.0001, end)

  oscillator.connect(gain)
  gain.connect(context.destination)
  oscillator.start(start)
  oscillator.stop(end)
}

/** One AudioContext for the whole page; browsers allow only a handful. */
function sharedContext(): AudioContext | null {
  if (shared) return shared
  const Constructor = globalThis.AudioContext
  if (!Constructor) return null
  shared = new Constructor()
  return shared
}
