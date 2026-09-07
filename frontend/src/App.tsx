import { apiBaseUrl } from './net/urls'
import './App.css'

/** Placeholder shell: proves the build is served and the API base resolves. */
function App() {
  const { http } = apiBaseUrl(window.location)

  return (
    <main>
      <h1>PushForm</h1>
      <p>Counting push-ups from your phone's camera. Nothing to see here yet.</p>
      <p>
        API base: <code>{http}</code>
      </p>
    </main>
  )
}

export default App
