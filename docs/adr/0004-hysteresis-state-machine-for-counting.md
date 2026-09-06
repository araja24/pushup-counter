# Hysteresis state machine for counting, not a learned model

Reps are counted by a two-phase machine over the median-smoothed elbow angle: enter DOWN below one threshold, leave DOWN above a higher one, count on leaving. Counting therefore needs no training data, is deterministic, is testable with synthetic motion, and is the same code that segments recordings into reps for training. The classifier only ever sees already-segmented reps.
