interface LiveScreenProps {
  onStop: () => void
}

/**
 * Placeholder for the set in progress. The counter, the connection and the
 * summary arrive with the live-counting ticket; this only proves the seam.
 */
export function LiveScreen({ onStop }: LiveScreenProps) {
  return (
    <main className="screen screen--prose">
      <h1>Set in progress</h1>
      <p>Counting is not wired up yet. This screen fills in with the next ticket.</p>
      <button type="button" onClick={onStop}>
        Stop
      </button>
    </main>
  )
}
