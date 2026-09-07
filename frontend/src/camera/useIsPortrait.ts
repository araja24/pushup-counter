import { useEffect, useState } from 'react'

const PORTRAIT = '(orientation: portrait)'

/** jsdom and older browsers have no matchMedia; assume landscape there. */
function portraitNow(): boolean {
  return typeof window.matchMedia === 'function' && window.matchMedia(PORTRAIT).matches
}

/** True while the phone is held upright, so the UI can ask for a rotation. */
export function useIsPortrait(): boolean {
  const [portrait, setPortrait] = useState(portraitNow)

  useEffect(() => {
    if (typeof window.matchMedia !== 'function') return

    const query = window.matchMedia(PORTRAIT)
    const onChange = (event: MediaQueryListEvent) => setPortrait(event.matches)
    query.addEventListener('change', onChange)
    return () => query.removeEventListener('change', onChange)
  }, [])

  return portrait
}
