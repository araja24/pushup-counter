import { useState } from 'react'

import { requestCameraStream } from '../camera/stream'

interface ExplainerScreenProps {
  onGranted: (stream: MediaStream) => void
}

/** Says why the camera is needed, before the browser's permission prompt. */
export function ExplainerScreen({ onGranted }: ExplainerScreenProps) {
  const [asking, setAsking] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const enableCamera = async () => {
    setAsking(true)
    setError(null)
    try {
      onGranted(await requestCameraStream())
    } catch (cause) {
      setError(explainFailure(cause))
      setAsking(false)
    }
  }

  return (
    <main className="screen screen--prose">
      <h1>PushForm</h1>
      <p className="lede">Counts your push-ups and tells you which ones had good form.</p>

      <h2>Why the camera</h2>
      <ul>
        <li>The camera watches you so the app can see your arms and back move.</li>
        <li>
          Your video never leaves the phone. Only the positions of 33 body points are sent
          for counting.
        </li>
        <li>The camera runs only while this page is open, and stops when you leave.</li>
      </ul>
      <p>Prop your phone up in landscape, about two metres away, side-on to your body.</p>

      <button type="button" onClick={() => void enableCamera()} disabled={asking}>
        {asking ? 'Waiting for permission...' : 'Turn on the camera'}
      </button>

      {error !== null && (
        <p role="alert" className="error">
          {error}
        </p>
      )}
    </main>
  )
}

function explainFailure(cause: unknown): string {
  const name = cause instanceof Error ? cause.name : ''
  if (name === 'NotAllowedError') {
    return 'Camera access was blocked. Allow the camera for this site in your browser settings, then try again.'
  }
  if (name === 'NotFoundError' || name === 'OverconstrainedError') {
    return 'No usable camera was found on this device.'
  }
  return cause instanceof Error ? cause.message : 'The camera could not be opened.'
}
