import type { ConnectionStatus } from '../net/socket'

interface ConnectionNoticeProps {
  status: ConnectionStatus
  /** The first health request is still unanswered past the waking-up delay. */
  probing: boolean
}

/**
 * The one line the user gets about the Connection, over whatever screen they
 * are on: the socket is being dialled back, or the backend is still waking up.
 * A healthy Connection says nothing at all.
 */
export function ConnectionNotice({ status, probing }: ConnectionNoticeProps) {
  if (status === 'reconnecting') return <Notice>Reconnecting…</Notice>
  if (status === 'waking' || probing) return <Notice>Waking up the server</Notice>
  return null
}

function Notice({ children }: { children: string }) {
  return (
    <p role="status" className="connection">
      {children}
    </p>
  )
}
