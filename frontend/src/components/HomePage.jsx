import { useState, useRef } from 'react';
import './HomePage.css';

export default function HomePage({ onUploadPdf, isUploading, uploadError }) {
    const [dragOver, setDragOver] = useState(false);
    const [error, setError] = useState('');
    const fileInputRef = useRef(null);

    const processFile = async (file) => {
        if (!file) return;

        const isPdf = file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf');
        if (!isPdf) {
            setError('Please upload a PDF file only.');
            return;
        }

        setError('');
        await onUploadPdf?.(file);
    };

    const handleDragOver = (e) => {
        e.preventDefault();
        setDragOver(true);
    };

    const handleDragLeave = () => setDragOver(false);

    const handleDrop = async (e) => {
        e.preventDefault();
        setDragOver(false);
        const file = e.dataTransfer.files?.[0];
        await processFile(file);
    };

    const handleUploadClick = () => {
        fileInputRef.current?.click();
    };

    return (
        <main className="home-page">
            <h1 className="home-hero-title">Drag &amp; Drop your PDF Form here</h1>
            <p className="home-hero-subtitle">We'll turn it into a simple voice conversation</p>

            <div
                className={`upload-zone ${dragOver ? 'drag-over' : ''}`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
                role="button"
                tabIndex={0}
                aria-label="Upload PDF form"
            >
                <input
                    type="file"
                    accept=".pdf"
                    className="upload-input-hidden"
                    ref={fileInputRef}
                    onChange={async (e) => {
                        await processFile(e.target.files?.[0]);
                    }}
                />

                <div className="upload-zone-icon">
                    <svg viewBox="0 0 80 80" fill="none">
                        <rect x="12" y="6" width="56" height="68" rx="6" fill="#e8f4f6" stroke="#2a7886" strokeWidth="2.5" />
                        <path d="M28 30h24M28 38h24M28 46h16" stroke="#2a7886" strokeWidth="2" strokeLinecap="round" />
                        <circle cx="56" cy="56" r="14" fill="#2a7886" />
                        <path d="M56 50v12M50 56h12" stroke="white" strokeWidth="2.5" strokeLinecap="round" />
                    </svg>
                </div>

                <div className="upload-zone-text">
                    <strong>Drag &amp; Drop</strong> your PDF Form here
                    <br />OR<br />
                    Click to <strong>Browse</strong>
                </div>

                <button
                    className="btn btn-primary upload-btn"
                    disabled={isUploading}
                    onClick={(e) => {
                        e.stopPropagation();
                        handleUploadClick();
                    }}
                >
                    {isUploading ? 'Uploading...' : 'Upload PDF'}
                </button>
            </div>

            {error && <p className="upload-error">{error}</p>}
            {uploadError && <p className="upload-error">{uploadError}</p>}

            <p className="upload-supported">Supported: Government forms, applications, intake forms &amp; more</p>
        </main>
    );
}
