import type { SummaryMessage } from '../net/socket'

interface SummaryScreenProps {
  summary: SummaryMessage
  /** Go back and do another Set, down the Connection that is already open. */
  onAnother: () => void
}

/** What the Set left behind: counted Reps, how long it took, and the pace. */
export function SummaryScreen({ summary, onAnother }: SummaryScreenProps) {
  return (
    <main className="screen screen--prose">
      <h1>Set complete</h1>

      <p className="count count--summary">{summary.reps}</p>
      <p className="lede">{summary.reps === 1 ? 'rep counted' : 'reps counted'}</p>

      <dl className="figures">
        <dt>Rejected</dt>
        <dd>{summary.rejected}</dd>
        <dt>Duration</dt>
        <dd>{seconds(summary.duration_ms)}</dd>
        <dt>Average rep</dt>
        <dd>{seconds(summary.avg_rep_ms)}</dd>
      </dl>

      <button type="button" onClick={onAnother}>
        Another set
      </button>
    </main>
  )
}

/** "12.4 s" -- milliseconds are backend units, not something a user reads. */
function seconds(ms: number): string {
  return `${(ms / 1000).toFixed(1)} s`
}
