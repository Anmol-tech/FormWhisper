/**
 * useFaceTracker — uses MediaPipe FaceDetector + webcam to track head position.
 * Face position is stored in a ref (not React state) so the RAF loop reads it
 * with zero latency — no setState → re-render → effect cycle on every frame.
 *
 * Usage:
 *   const { posRef, isTracking, isLoading, error, start, stop, videoRef } = useFaceTracker();
 *   // posRef.current = { x: 0–1, y: 0–1 }  (0.5 = center)
 */
import { useRef, useState, useCallback, useEffect } from 'react';
import { FaceDetector, FilesetResolver } from '@mediapipe/tasks-vision';

// MediaPipe WASM and model are loaded from CDN — version must match installed package (0.10.32)
const MEDIAPIPE_WASM_URL =
  'https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.32/wasm';
const MODEL_URL =
  'https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite';

export function useFaceTracker() {
  const videoRef    = useRef(null);
  const detectorRef = useRef(null);
  const rafRef      = useRef(null);
  const streamRef   = useRef(null);

  // Face position stored as a plain ref — updated every frame with no React overhead
  // posRef stores delta from the calibrated neutral, re-centered at 0.5
  const posRef     = useRef({ x: 0.5, y: 0.5 });
  const neutralRef = useRef(null); // set on first detection after start()

  const [isTracking, setIsTracking] = useState(false);
  const [isLoading,  setIsLoading]  = useState(false);
  const [error,      setError]      = useState(null);

  // ── Init MediaPipe detector (lazy, only once) ──────────────────────────────
  const initDetector = useCallback(async () => {
    if (detectorRef.current) return; // already initialized
    const filesetResolver = await FilesetResolver.forVisionTasks(MEDIAPIPE_WASM_URL);
    // Try GPU first, fall back to CPU if not supported
    try {
      detectorRef.current = await FaceDetector.createFromOptions(filesetResolver, {
        baseOptions: { modelAssetPath: MODEL_URL, delegate: 'GPU' },
        runningMode: 'VIDEO',
      });
    } catch {
      detectorRef.current = await FaceDetector.createFromOptions(filesetResolver, {
        baseOptions: { modelAssetPath: MODEL_URL, delegate: 'CPU' },
        runningMode: 'VIDEO',
      });
    }
  }, []);

  // ── Detection loop ─────────────────────────────────────────────────────────
  const detect = useCallback(() => {
    const video = videoRef.current;
    const detector = detectorRef.current;
    if (!video || !detector || video.readyState < 2) {
      rafRef.current = requestAnimationFrame(detect);
      return;
    }

    const result = detector.detectForVideo(video, performance.now());

    if (result.detections.length > 0) {
      const box = result.detections[0].boundingBox;
      const cx = (box.originX + box.width / 2) / video.videoWidth;
      const cy = (box.originY + box.height / 2) / video.videoHeight;
      const rawX = 1 - cx; // mirror X for selfie view
      const rawY = cy;

      // First detection after start → set as the neutral (straight) position
      if (!neutralRef.current) {
        neutralRef.current = { x: rawX, y: rawY };
      }

      // Store delta from neutral, re-centered at 0.5 so component math stays unchanged
      posRef.current = {
        x: 0.5 + (rawX - neutralRef.current.x),
        y: 0.5 + (rawY - neutralRef.current.y),
      };
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
      console.error('[FaceTracker] Model load failed:', err);
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
      console.error('[FaceTracker] Camera access failed:', err);
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
    posRef.current     = { x: 0.5, y: 0.5 };
    neutralRef.current = null; // reset so next start() re-calibrates
    setIsTracking(false);
  }, []);

  useEffect(() => () => stop(), [stop]);

  return { posRef, isTracking, isLoading, error, start, stop, videoRef };
}
