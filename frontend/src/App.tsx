import { useEffect, useRef, useState } from 'react'

import { ReconnectingSocket } from './net/reconnect'
import type { ConnectionStatus, SummaryMessage } from './net/socket'
import { apiBaseUrl, frameSocketUrl } from './net/urls'
import { probeHealth } from './net/wakeup'
import { ConnectionNotice } from './screens/ConnectionNotice'
import { ExplainerScreen } from './screens/ExplainerScreen'
import { LiveScreen } from './screens/LiveScreen'
import { PositioningScreen } from './screens/PositioningScreen'
import { SummaryScreen } from './screens/SummaryScreen'
import './App.css'

/** Whatever a stage needs of the Connection every Set on it shares. */
interface Streaming {
  stream: MediaStream
  socket: ReconnectingSocket
}

type Stage =
  | { name: 'explainer' }
  | ({ name: 'positioning' } & Streaming)
  | ({ name: 'live' } & Streaming)
  | ({ name: 'summary'; summary: SummaryMessage } & Streaming)

/**
 * Explainer, then positioning, then the Set, then its Summary. The camera
 * stream follows along, and one Connection outlives every Set on it -- including
 * the sockets it loses on the way, which it dials back and resumes.
 */
function App() {
  const [stage, setStage] = useState<Stage>({ name: 'explainer' })
  const [status, setStatus] = useState<ConnectionStatus>('connecting')
  const [probing, setProbing] = useState(false)
  const connection = useRef<ReconnectingSocket | null>(null)

  useEffect(() => () => connection.current?.close(), [])

  useEffect(() => {
    // The backend sleeps when nobody has used it. Knocking while the user reads
    // this page wakes it, and says so if the knock goes unanswered long enough
    // for the app to look broken.
    void probeHealth(`${apiBaseUrl(window.location).http}/api/health`, { onWaking: setProbing })
  }, [])

  /** Opened once the camera is granted, and held until the page goes away. */
  const openConnection = (): ReconnectingSocket => {
    if (connection.current === null) {
      const socket = new ReconnectingSocket(frameSocketUrl(window.location))
      socket.listenStatus(setStatus)
      connection.current = socket
    }
    return connection.current
  }

  /** The screen the user is on. One Connection carries all of them. */
  const stageScreen = () => {
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

  return (
    <>
      <ConnectionNotice status={status} probing={probing} />
      {stageScreen()}
    </>
  )
}

export default App
