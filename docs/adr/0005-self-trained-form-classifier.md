# Self-trained form classifier over a sourced model

Ready-made exercise-form models on Hugging Face were considered and rejected: they are video classifiers without per-rep reasoning, or trained on data that does not match a phone selfie camera side view. We collect and label our own reps and train a scikit-learn model. More work, but it fits the deployment conditions exactly and gives a defensible answer to "what did you train?"
