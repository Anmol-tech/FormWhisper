/**
 * useHandTracker — uses MediaPipe HandLandmarker + webcam to track palm position.
 * Returns normalized palm center X/Y (0-1) so the caller can map it to 3D rotation.
 *
 * Palm center = average of wrist + 4 knuckle base landmarks (stable, not fingertip-jittery).
 *
 * Usage:
 *   const { palmX, palmY, isTracking, isLoading, error, start, stop, videoRef } = useHandTracker();
 */
import { useRef, useState, useCallback, useEffect } from 'react';
import { HandLandmarker, FilesetResolver } from '@mediapipe/tasks-vision';

const MEDIAPIPE_WASM_URL =
  'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.32/wasm';
const MODEL_URL =
  'https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task';

// Landmark indices that form a stable palm center
// 0=WRIST, 5=INDEX_MCP, 9=MIDDLE_MCP, 13=RING_MCP, 17=PINKY_MCP
const PALM_INDICES = [0, 5, 9, 13, 17];

export function useHandTracker() {
  const videoRef    = useRef(null);
  const detectorRef = useRef(null);
  const rafRef      = useRef(null);
  const streamRef   = useRef(null);

  const [isTracking, setIsTracking] = useState(false);
  const [isLoading,  setIsLoading]  = useState(false);
  const [error,      setError]      = useState(null);

  // Normalized palm center (0–1). 0.5 = center of frame.
  const [palmX, setPalmX] = useState(0.5);
  const [palmY, setPalmY] = useState(0.5);

  // ── Init HandLandmarker (lazy, once) ───────────────────────────────────────
  const initDetector = useCallback(async () => {
    if (detectorRef.current) return;
    const filesetResolver = await FilesetResolver.forVisionTasks(MEDIAPIPE_WASM_URL);
    try {
      detectorRef.current = await HandLandmarker.createFromOptions(filesetResolver, {
        baseOptions: { modelAssetPath: MODEL_URL, delegate: 'GPU' },
        runningMode: 'VIDEO',
        numHands: 1,
      });
    } catch {
      detectorRef.current = await HandLandmarker.createFromOptions(filesetResolver, {
        baseOptions: { modelAssetPath: MODEL_URL, delegate: 'CPU' },
        runningMode: 'VIDEO',
        numHands: 1,
      });
    }
  }, []);

  // ── Detection loop ─────────────────────────────────────────────────────────
  const detect = useCallback(() => {
    const video    = videoRef.current;
    const detector = detectorRef.current;

    if (!video || !detector || video.readyState < 2) {
      rafRef.current = requestAnimationFrame(detect);
      return;
    }

    const result = detector.detectForVideo(video, performance.now());

    if (result.landmarks && result.landmarks.length > 0) {
      const landmarks = result.landmarks[0]; // first hand

      // Average the palm landmark positions for a stable center
      let sumX = 0, sumY = 0;
      PALM_INDICES.forEach(i => {
        sumX += landmarks[i].x;
        sumY += landmarks[i].y;
      });
      const cx = sumX / PALM_INDICES.length;
      const cy = sumY / PALM_INDICES.length;

      // Mirror X — webcam feed is mirrored (selfie view)
      setPalmX(1 - cx);
      setPalmY(cy);
    }

    rafRef.current = requestAnimationFrame(detect);
  }, []);

  // ── Start tracking ─────────────────────────────────────────────────────────
  const start = useCallback(async () => {
    setError(null);
    setIsLoading(true);

    try {
      await initDetector();
    } catch (err) {
      setIsLoading(false);
      console.error('[HandTracker] Model load failed:', err);
      setError(`Model failed to load: ${err.message || err}. Check your internet connection.`);
      return;
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'user' },
        audio: false,
      });
      streamRef.current = stream;

      const video = videoRef.current;
      if (video) {
        video.srcObject = stream;
        await video.play();
      }

      setIsTracking(true);
      setIsLoading(false);
      rafRef.current = requestAnimationFrame(detect);
    } catch (err) {
      setIsLoading(false);
      console.error('[HandTracker] Camera access failed:', err);
      const msg =
        err.name === 'NotAllowedError'  ? 'Camera permission denied — allow it in browser settings and refresh' :
        err.name === 'NotFoundError'    ? 'No camera found on this device' :
        err.name === 'NotReadableError' ? 'Camera is in use by another app — close other apps using the camera' :
        `Camera error (${err.name}): ${err.message}`;
      setError(msg);
    }
  }, [initDetector, detect]);

  // ── Stop tracking ──────────────────────────────────────────────────────────
  const stop = useCallback(() => {
    if (rafRef.current) cancelAnimationFrame(rafRef.current);
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop());
      streamRef.current = null;
    }
    const video = videoRef.current;
    if (video) video.srcObject = null;
    setIsTracking(false);
    setPalmX(0.5);
    setPalmY(0.5);
  }, []);

  // Cleanup on unmount
  useEffect(() => () => stop(), [stop]);

  return { palmX, palmY, isTracking, isLoading, error, start, stop, videoRef };
}
