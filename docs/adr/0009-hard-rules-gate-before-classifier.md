# Hard rules decide first, the classifier decides the grey zone

Per-frame hip alignment and rep-end elbow depth are checked by deterministic hard rules with conservative thresholds. A rep that trips a hard rule is rejected without consulting the classifier. Only reps inside the grey zone, where no hard rule fires, are labelled by the trained model. This gives working form feedback from the first milestone with no model, keeps the live red/green skeleton deterministic, and focuses the small self-collected dataset on the borderline reps where a learned decision is worth having.

## Consequences

The classifier can reject a rep that stayed green throughout, so every classifier rejection carries a reason shown to the user. To keep the gate strict but not punitive, the classifier rejects only when its predicted fault probability is at least 0.7; below that the rep counts. The floor lives in `analysis/config.py` beside the thresholds.
