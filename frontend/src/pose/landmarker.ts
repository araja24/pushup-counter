/**
 * The only module that touches MediaPipe.
 *
 * Everything else works with plain landmarks, so tests never import
 * `@mediapipe/tasks-vision`. Import this lazily from an effect -- the WASM
 * runtime and the model are fetched at runtime, not bundled.
 */

import { FilesetResolver, PoseLandmarker } from '@mediapipe/tasks-vision'

import type { PoseLandmark } from './wire'

/** The Tasks Vision WASM runtime, pinned to the version in package.json. */
const WASM_BASE = 'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@1.0.1/wasm'

/** The lite pose model, from Google's official model storage. */
const MODEL_URL =
  'https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task'

/** Which processor MediaPipe ended up running the model on. */
export type Delegate = 'GPU' | 'CPU'

export interface PoseTracker {
  /** The landmarks for the one body in this video frame, or null if none. */
  detect(video: HTMLVideoElement, timestampMs: number): PoseLandmark[] | null
  close(): void
  readonly delegate: Delegate
}

/**
 * Start the landmarker, preferring the GPU delegate and falling back to CPU
 * on phones where WebGL is unavailable or the GPU build fails to build.
 */
export async function createPoseTracker(): Promise<PoseTracker> {
  const fileset = await FilesetResolver.forVisionTasks(WASM_BASE)

  let lastError: unknown
  for (const delegate of ['GPU', 'CPU'] as const) {
    try {
      const landmarker = await PoseLandmarker.createFromOptions(fileset, {
        baseOptions: { modelAssetPath: MODEL_URL, delegate },
        runningMode: 'VIDEO',
        numPoses: 1,
      })
      return {
        delegate,
        detect: (video, timestampMs) =>
          landmarker.detectForVideo(video, timestampMs).landmarks[0] ?? null,
        close: () => landmarker.close(),
      }
    } catch (error) {
      lastError = error
    }
  }

  throw new Error(`Pose landmarker failed to start: ${String(lastError)}`)
}
