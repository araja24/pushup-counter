# Tabular per-rep classifier with a single label per rep

Form is assessed once per rep from a fixed feature vector of angle statistics, not by a sequence model over frames, and each rep receives exactly one label from `{good, partial_rom, hip_sag, hip_pike}` rather than a set of independent faults. A roughly 160-rep self-collected dataset cannot support a sequence model or three separate binary classifiers, and a single label keeps the collection protocol simple: one intended label per recording.

## Consequences

A rep that is both short and sagging gets one label, and the partial-range hard rule wins when it fires.
