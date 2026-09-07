/**
 * Getting the selfie camera, and asking the phone to stay in landscape.
 */

/** Selfie camera, 30 fps, 720p -- enough for landmarks without wasting battery. */
export const CAMERA_CONSTRAINTS: MediaStreamConstraints = {
  video: {
    facingMode: 'user',
    frameRate: { ideal: 30 },
    width: { ideal: 1280 },
    height: { ideal: 720 },
  },
  audio: false,
}

/** Prompt for the camera. Rejects if the user denies it or none is available. */
export function requestCameraStream(): Promise<MediaStream> {
  if (!navigator.mediaDevices?.getUserMedia) {
    return Promise.reject(
      new Error('This browser cannot open the camera. Try Chrome or Safari over HTTPS.'),
    )
  }
  return navigator.mediaDevices.getUserMedia(CAMERA_CONSTRAINTS)
}

/**
 * Ask the browser to hold the phone in landscape. Resolves false where the
 * Screen Orientation lock API is missing (notably iOS Safari) or refused, in
 * which case the UI falls back to a "rotate your phone" hint.
 */
export async function lockLandscape(): Promise<boolean> {
  const orientation = screen.orientation as ScreenOrientation & {
    lock?: (orientation: string) => Promise<void>
  }
  if (typeof orientation?.lock !== 'function') return false

  try {
    await orientation.lock('landscape')
    return true
  } catch {
    return false
  }
}
