/**
 * The one thing the screen says when the backend cannot count for the user.
 *
 * A pure function of a State message so the wording and the precedence can be
 * tested without a camera, a socket or a rendered screen. The screen's job is
 * only to show whatever comes back.
 *
 * Words, never colour alone: a user face-down on the floor at arm's length
 * from a phone is reading shapes at a glance, and some of them cannot tell red
 * from green at all.
 */

import type { StateMessage } from '../net/socket'

/** Tracking is Lost: the camera has lost the arm it was measuring. */
export const CANT_SEE_YOU = "Can't see you"

/** A Stall: the elbows have sat between the two thresholds for too long. */
export const LOCK_OUT = 'Lock out your arms'

/**
 * What to tell the user about this State, or null when nothing is wrong.
 *
 * Tracking comes first. A Stall reported while the user is out of shot is a
 * reading of the last angle anyone saw, and no amount of locking out fixes a
 * camera that cannot see them.
 */
export function cueFor(state: Pick<StateMessage, 'tracking' | 'stalled'>): string | null {
  if (!state.tracking) return CANT_SEE_YOU
  if (state.stalled) return LOCK_OUT
  return null
}
