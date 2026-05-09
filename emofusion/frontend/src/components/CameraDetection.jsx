import React, { useState, useRef, useEffect, useCallback } from "react";
import api from "../utils/api";
import EmotionResult from "./EmotionResult";
import Spinner from "./Spinner";

export default function CameraDetection({ onResult, onOpenModal, onStartBreathing }) {
  const [cameraOn, setCameraOn] = useState(false);
  const [captured, setCaptured] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [autoMode, setAutoMode] = useState(false);
  const [countdown, setCountdown] = useState(null);

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);
  const autoTimerRef = useRef(null);
  const countdownRef = useRef(null);

  const startCamera = async () => {
    setError("");
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480, facingMode: "user" },
      });
      streamRef.current = stream;
      if (videoRef.current) videoRef.current.srcObject = stream;
      setCameraOn(true);
      setCaptured(null);
      setResult(null);
    } catch {
      setError("Camera access denied. Please allow camera permissions in your browser.");
    }
  };

  const stopCamera = () => {
    streamRef.current?.getTracks().forEach((t) => t.stop());
    streamRef.current = null;
    setCameraOn(false);
    setAutoMode(false);
    clearInterval(autoTimerRef.current);
    clearInterval(countdownRef.current);
    setCountdown(null);
  };

  const captureFrame = useCallback(() => {
    const video = videoRef.current;
    const canvas = canvasRef.current;
    if (!video || !canvas) return null;
    const ctx = canvas.getContext("2d");
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    ctx.drawImage(video, 0, 0);
    const dataUrl = canvas.toDataURL("image/jpeg", 0.9);
    setCaptured(dataUrl);
    return dataUrl;
  }, []);

  const analyze = useCallback(async (dataUrl) => {
    const url = dataUrl || captured;
    if (!url) return;
    setLoading(true); setError(""); setResult(null);
    try {
      const blob = await (await fetch(url)).blob();
      const form = new FormData();
      form.append("image", blob, "capture.jpg");
      const { data } = await api.post("/predict-face", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResult(data);
      onResult?.(data);
    } catch (e) {
      setError(e.response?.data?.error || "Face analysis failed.");
    } finally {
      setLoading(false);
    }
  }, [captured, onResult]);

  const captureAndAnalyze = () => {
    const url = captureFrame();
    if (url) analyze(url);
  };

  // Auto-detect mode
  useEffect(() => {
    if (autoMode && cameraOn) {
      setCountdown(4);
      countdownRef.current = setInterval(() => setCountdown((c) => (c <= 1 ? 4 : c - 1)), 1000);
      autoTimerRef.current = setInterval(() => {
        const url = captureFrame();
        if (url) analyze(url);
      }, 4000);
    } else {
      clearInterval(autoTimerRef.current);
      clearInterval(countdownRef.current);
      setCountdown(null);
    }
    return () => { clearInterval(autoTimerRef.current); clearInterval(countdownRef.current); };
  }, [autoMode, cameraOn, captureFrame, analyze]);

  useEffect(() => () => stopCamera(), []);

  return (
    <div className="space-y-6">
      {/* Camera feed */}
      <div className="relative rounded-2xl overflow-hidden bg-surface-dark border border-surface-border aspect-video">
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className={`w-full h-full object-cover ${cameraOn ? "block" : "hidden"}`}
        />
        <canvas ref={canvasRef} className="hidden" />

        {!cameraOn && !captured && (
          <div className="absolute inset-0 flex flex-col items-center justify-center gap-4">
            <div className="text-6xl opacity-30">📷</div>
            <p className="text-gray-500 text-sm">Camera is off</p>
          </div>
        )}

        {captured && !cameraOn && (
          <img src={captured} alt="Captured frame" className="w-full h-full object-cover" />
        )}

        {/* Face frame overlay */}
        {cameraOn && (
          <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
            <div className="w-48 h-56 border-2 border-brand-500/60 rounded-2xl relative">
              <div className="absolute -top-0.5 -left-0.5 w-4 h-4 border-t-2 border-l-2 border-brand-400 rounded-tl" />
              <div className="absolute -top-0.5 -right-0.5 w-4 h-4 border-t-2 border-r-2 border-brand-400 rounded-tr" />
              <div className="absolute -bottom-0.5 -left-0.5 w-4 h-4 border-b-2 border-l-2 border-brand-400 rounded-bl" />
              <div className="absolute -bottom-0.5 -right-0.5 w-4 h-4 border-b-2 border-r-2 border-brand-400 rounded-br" />
            </div>
          </div>
        )}

        {/* Countdown badge */}
        {autoMode && countdown !== null && (
          <div className="absolute top-3 right-3 w-10 h-10 rounded-full bg-brand-500 flex items-center justify-center font-display font-bold text-white text-lg">
            {countdown}
          </div>
        )}

        {/* Auto indicator */}
        {autoMode && (
          <div className="absolute top-3 left-3 px-3 py-1 rounded-full bg-green-500/20 border border-green-500/40 text-xs text-green-400 flex items-center gap-1.5">
            <span className="w-1.5 h-1.5 rounded-full bg-green-400 animate-ping" />
            Auto Detect
          </div>
        )}
      </div>

      {error && (
        <div className="rounded-xl bg-red-500/10 border border-red-500/30 px-4 py-3 text-sm text-red-400">⚠️ {error}</div>
      )}

      {/* Controls */}
      <div className="flex flex-wrap gap-3">
        {!cameraOn ? (
          <button
            onClick={startCamera}
            className="flex-1 py-3 rounded-xl bg-brand-500 hover:bg-brand-600 text-white font-semibold text-sm transition-colors"
          >
            📷 Start Camera
          </button>
        ) : (
          <>
            <button
              onClick={captureAndAnalyze}
              disabled={loading}
              className="flex-1 py-3 rounded-xl bg-brand-500 hover:bg-brand-600 disabled:opacity-40 text-white font-semibold text-sm transition-colors"
            >
              🔍 Capture & Analyze
            </button>
            <button
              onClick={() => setAutoMode((a) => !a)}
              className={`px-5 py-3 rounded-xl font-semibold text-sm transition-colors border
                ${autoMode
                  ? "bg-green-500/20 border-green-500/40 text-green-400"
                  : "bg-white/5 border-surface-border text-gray-300 hover:text-white"}`}
            >
              {autoMode ? "⏸ Stop Auto" : "▶ Auto Detect"}
            </button>
            <button
              onClick={stopCamera}
              className="px-4 py-3 rounded-xl bg-red-500/10 border border-red-500/30 text-red-400 hover:bg-red-500/20 text-sm transition-colors"
            >
              ✕
            </button>
          </>
        )}
      </div>

      {loading && <Spinner label="Detecting facial expressions…" />}
      {result && <EmotionResult result={result} onOpenModal={onOpenModal} onStartBreathing={onStartBreathing} />}
    </div>
  );
}
