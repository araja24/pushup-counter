import { useEffect, useRef, useState } from 'react'

import { FrameSocket } from './net/socket'
import type { SummaryMessage } from './net/socket'
import { frameSocketUrl } from './net/urls'
import { ExplainerScreen } from './screens/ExplainerScreen'
import { LiveScreen } from './screens/LiveScreen'
import { PositioningScreen } from './screens/PositioningScreen'
import { SummaryScreen } from './screens/SummaryScreen'
import './App.css'

/** Whatever a stage needs of the Connection every Set on it shares. */
interface Streaming {
  stream: MediaStream
  socket: FrameSocket
}

type Stage =
  | { name: 'explainer' }
  | ({ name: 'positioning' } & Streaming)
  | ({ name: 'live' } & Streaming)
  | ({ name: 'summary'; summary: SummaryMessage } & Streaming)

/**
 * Explainer, then positioning, then the Set, then its Summary. The camera
 * stream follows along, and one Connection outlives every Set on it.
 */
function App() {
  const [stage, setStage] = useState<Stage>({ name: 'explainer' })
  const connection = useRef<FrameSocket | null>(null)

  useEffect(() => () => connection.current?.close(), [])

  /** Opened once the camera is granted, and held until the page goes away. */
  const openConnection = (): FrameSocket => {
    connection.current ??= new FrameSocket(frameSocketUrl(window.location))
    return connection.current
  }

  switch (stage.name) {
    case 'explainer':
      return (
        <ExplainerScreen
          onGranted={(stream) =>
            setStage({ name: 'positioning', stream, socket: openConnection() })
          }
        />
      )
    case 'positioning':
      return (
        <PositioningScreen
          stream={stage.stream}
          socket={stage.socket}
          onStart={() => setStage({ ...stage, name: 'live' })}
        />
      )
    case 'live':
      return (
        <LiveScreen
          stream={stage.stream}
          socket={stage.socket}
          onFinished={(summary) => setStage({ ...stage, name: 'summary', summary })}
        />
      )
    case 'summary':
      return (
        <SummaryScreen
          summary={stage.summary}
          onAnother={() =>
            setStage({ name: 'positioning', stream: stage.stream, socket: stage.socket })
          }
        />
      )
  }
}

export default App
