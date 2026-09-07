import { useState } from 'react'

import { ExplainerScreen } from './screens/ExplainerScreen'
import { LiveScreen } from './screens/LiveScreen'
import { PositioningScreen } from './screens/PositioningScreen'
import './App.css'

type Stage =
  | { name: 'explainer' }
  | { name: 'positioning'; stream: MediaStream }
  | { name: 'live'; stream: MediaStream }

/** Explainer, then positioning, then the set. The camera stream follows along. */
function App() {
  const [stage, setStage] = useState<Stage>({ name: 'explainer' })

  switch (stage.name) {
    case 'explainer':
      return (
        <ExplainerScreen
          onGranted={(stream) => setStage({ name: 'positioning', stream })}
        />
      )
    case 'positioning':
      return (
        <PositioningScreen
          stream={stage.stream}
          onStart={(stream) => setStage({ name: 'live', stream })}
        />
      )
    case 'live':
      return (
        <LiveScreen
          onStop={() => setStage({ name: 'positioning', stream: stage.stream })}
        />
      )
  }
}

export default App
