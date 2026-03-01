/**
 * SpatialPDFView — shows the FEMA form as a 3D spatial card using WebSpatial.
 * In normal browser: renders as a 3D tilting card with depth + face/trackpad tracking.
 * In visionOS simulator (XR_ENV=avp): the card and fields float in real 3D space.
 */
import { useRef, useCallback, useEffect, useState } from 'react';
import { useFaceTracker } from '../hooks/useFaceTracker';
import './SpatialPDFView.css';

const FEMA_QUESTIONS = [
  { id: 1, label: 'What is your full legal name?', fieldName: 'applicant_name' },
  { id: 2, label: 'What is your date of birth?', fieldName: 'date_of_birth' },
  { id: 3, label: 'What is your Social Security Number?', fieldName: 'ssn' },
  { id: 4, label: 'What is your current mailing address?', fieldName: 'mailing_address' },
  { id: 5, label: 'What is your phone number?', fieldName: 'phone_number' },
  { id: 6, label: 'What type of disaster affected you?', fieldName: 'disaster_type' },
  { id: 7, label: 'What is the address of the damaged property?', fieldName: 'damaged_property_address' },
  { id: 8, label: 'Do you have insurance coverage for the damaged property?', fieldName: 'has_insurance' },
];

export default function SpatialPDFView({ answers = {}, currentIndex = 0 }) {
  const questions = FEMA_QUESTIONS;
  const cardRef = useRef(null);

  // ── Face tracking ──────────────────────────────────────────────────────────
  const { posRef, isTracking, isLoading, error, start, stop, videoRef } = useFaceTracker();  const [showCamPrompt, setShowCamPrompt] = useState(false);
  // Apply card rotation from face position each frame while face tracking is on
  useEffect(() => {
    if (!isTracking) return;
    let raf;
    const loop = () => {
      const card = cardRef.current;
      if (card) {
        if (card.style.animation !== 'none') card.style.animation = 'none';
        card.style.transition = 'none';
        // Face delta from neutral is tiny (±0.05–0.1) vs trackpad's full 0–1 range.
        // Use much higher multiplier to match the visual impact of the trackpad.
        const { x, y } = posRef.current;
        const rotateY = Math.max(-45, Math.min(45, (x - 0.5) * 240));
        const rotateX = Math.max(-35, Math.min(35, (y - 0.5) * 180)); // inverted: head up → card tilts toward you
        card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateZ(24px) scale(1.01)`;
      }
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [isTracking, posRef]);

  // ── Trackpad / pointer tracking (used when face track is OFF) ──────────────
  const handlePointerMove = useCallback((e) => {
    if (isTracking) return;
    const card = cardRef.current;
    if (!card) return;
    if (card.style.animation !== 'none') card.style.animation = 'none';
    card.style.transition = 'none';
    const x = e.clientX / window.innerWidth;
    const y = e.clientY / window.innerHeight;
    const rotateX = (0.5 - y) * 40;
    const rotateY = (x - 0.5) * 56;
    card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateZ(24px) scale(1.01)`;
  }, [isTracking]);

  const handlePointerLeave = useCallback(() => {
    if (isTracking) return;
    const card = cardRef.current;
    if (!card) return;
    card.style.transition = 'transform 0.6s cubic-bezier(0.23, 1, 0.32, 1)';
    card.style.transform = 'perspective(1000px) rotateX(4deg) rotateY(-3deg) translateZ(0px)';
  }, [isTracking]);

  // ── Camera permission flow ─────────────────────────────────────────────────
  const handleFaceTrackClick = () => {
    if (isTracking) { stop(); return; }
    setShowCamPrompt(true);
  };

  const handleGrantCamera = async () => {
    setShowCamPrompt(false);
    await start();
  };

  return (
    <div
      className="spatial-page"
      onPointerMove={isTracking ? undefined : handlePointerMove}
      onPointerLeave={isTracking ? undefined : handlePointerLeave}
    >
      <div className="spatial-header">
        <h1 className="spatial-title">FormWhisper</h1>
        <p className="spatial-subtitle">3D Spatial Form View</p>
        <p className="spatial-hint">
          📱 In visionOS: fields float in 3D space &nbsp;|&nbsp; 🖥️ In browser: move your head or trackpad
        </p>

        {/* Face Track toggle */}
        <div className="face-track-controls">
          <button
            className={`face-track-btn ${isTracking ? 'active' : ''} ${isLoading ? 'loading' : ''}`}
            onClick={handleFaceTrackClick}
            disabled={isLoading}
          >
            {isLoading ? '⏳ Loading model…' : isTracking ? '🎥 Face Track ON' : '🎥 Enable Face Track'}
          </button>
          {error && (
            <div className="face-track-error">
              <span>⚠️ {error}</span>
              {error.includes('permission') && (
                <span className="face-track-fix">
                  Click the 🔒 lock icon in your browser address bar → Camera → Allow → refresh.
                </span>
              )}
            </div>
          )}

          {/* Camera permission prompt card */}
          {showCamPrompt && (
            <div className="cam-prompt-card">
              <p className="cam-prompt-title">📷 Camera Access Needed</p>
              <p className="cam-prompt-body">
                Face tracking uses your webcam to rotate the form as you move your head.
                Your camera feed never leaves your device.
              </p>
              <div className="cam-prompt-actions">
                <button className="cam-prompt-allow" onClick={handleGrantCamera}>Allow Camera</button>
                <button className="cam-prompt-deny" onClick={() => setShowCamPrompt(false)}>Cancel</button>
              </div>
            </div>
          )}

          {/* Single video element — MediaPipe reads from it, also shown as preview */}
          <div className={`face-track-preview ${isTracking ? 'visible' : ''}`}>
            <video
              ref={videoRef}
              autoPlay
              muted
              playsInline
              className="face-track-video"
            />
            {isTracking && <span className="face-track-label">● Live</span>}
          </div>
        </div>
      </div>

      {/* Main form card — spatialized with enable-xr */}
      <div
        className="spatial-form-card"
        enable-xr=""
        ref={cardRef}
      >
        {/* PDF Header */}
        <div className="spatial-form-header">
          <div className="spatial-agency-badge">FEMA</div>
          <div>
            <h2>FEMA Disaster Aid Form</h2>
            <p>Form 009-0-3</p>
          </div>
        </div>

        {/* Form Fields — each field is individually spatialized */}
        <div className="spatial-fields">
          {questions.map((q, i) => {
            const isFilled = !!answers[q.fieldName];
            const isActive = i === currentIndex;

            return (
              <div
                key={q.id}
                className={`spatial-field ${isActive ? 'active' : ''} ${isFilled ? 'filled' : ''}`}
                enable-xr=""
              >
                <span className="spatial-field-number">{q.id}</span>
                <div className="spatial-field-content">
                  <span className="spatial-field-label">{q.label}</span>
                  {isFilled && (
                    <span className="spatial-field-value">{answers[q.fieldName]}</span>
                  )}
                  {isActive && !isFilled && (
                    <span className="spatial-field-active-badge">▶ Current</span>
                  )}
                </div>
                <span className={`spatial-field-status ${isFilled ? 'done' : isActive ? 'now' : 'empty'}`}>
                  {isFilled ? '✓' : isActive ? '●' : '○'}
                </span>
              </div>
            );
          })}
        </div>

        {/* Progress */}
        <div className="spatial-progress-bar">
          <div
            className="spatial-progress-fill"
            style={{ width: `${(Object.keys(answers).length / questions.length) * 100}%` }}
          />
        </div>
        <p className="spatial-progress-label">
          {Object.keys(answers).length} of {questions.length} fields completed
        </p>
      </div>
    </div>
  );
}
