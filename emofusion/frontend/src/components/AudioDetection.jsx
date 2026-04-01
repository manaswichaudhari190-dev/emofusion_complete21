import React, { useState, useRef, useEffect } from "react";
import api from "../utils/api";
import EmotionResult from "./EmotionResult";
import Spinner from "./Spinner";

export default function AudioDetection({ onResult }) {
  const [mode, setMode] = useState("upload"); // "upload" | "record"
  const [recording, setRecording] = useState(false);
  const [audioBlob, setAudioBlob] = useState(null);
  const [audioURL, setAudioURL] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [duration, setDuration] = useState(0);
  const [waveData, setWaveData] = useState(new Array(40).fill(4));

  const mediaRef = useRef(null);
  const chunksRef = useRef([]);
  const timerRef = useRef(null);
  const analyserRef = useRef(null);
  const animRef = useRef(null);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const ctx = new AudioContext();
      const src = ctx.createMediaStreamSource(stream);
      const analyser = ctx.createAnalyser();
      analyser.fftSize = 128;
      src.connect(analyser);
      analyserRef.current = analyser;

      const drawWave = () => {
        const buf = new Uint8Array(analyser.frequencyBinCount);
        analyser.getByteFrequencyData(buf);
        const bars = Array.from({ length: 40 }, (_, i) =>
          Math.max(4, Math.floor((buf[Math.floor(i * buf.length / 40)] / 255) * 60))
        );
        setWaveData(bars);
        animRef.current = requestAnimationFrame(drawWave);
      };
      drawWave();

      const mr = new MediaRecorder(stream);
      chunksRef.current = [];
      mr.ondataavailable = (e) => chunksRef.current.push(e.data);
      mr.onstop = () => {
        stream.getTracks().forEach((t) => t.stop());
        cancelAnimationFrame(animRef.current);
        setWaveData(new Array(40).fill(4));
        const blob = new Blob(chunksRef.current, { type: "audio/webm" });
        setAudioBlob(blob);
        setAudioURL(URL.createObjectURL(blob));
      };
      mr.start();
      mediaRef.current = mr;
      setRecording(true);
      setDuration(0);
      setResult(null);
      timerRef.current = setInterval(() => setDuration((d) => d + 1), 1000);
    } catch {
      setError("Microphone access denied. Please allow microphone permissions.");
    }
  };

  const stopRecording = () => {
    mediaRef.current?.stop();
    clearInterval(timerRef.current);
    setRecording(false);
  };

  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setAudioBlob(file);
    setAudioURL(URL.createObjectURL(file));
    setResult(null);
    setError("");
  };

  const analyze = async () => {
    if (!audioBlob) return setError("No audio to analyze.");
    setLoading(true); setError(""); setResult(null);
    const form = new FormData();
    form.append("audio", audioBlob, "recording.webm");
    try {
      const { data } = await api.post("/predict-audio", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResult(data);
      onResult?.(data);
    } catch (e) {
      setError(e.response?.data?.error || "Audio analysis failed.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => () => { clearInterval(timerRef.current); cancelAnimationFrame(animRef.current); }, []);

  return (
    <div className="space-y-6">
      {/* Mode tabs */}
      <div className="flex gap-2 p-1 bg-surface-dark rounded-xl border border-surface-border w-fit">
        {["upload", "record"].map((m) => (
          <button
            key={m}
            onClick={() => { setMode(m); setResult(null); setAudioBlob(null); setAudioURL(""); setError(""); }}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors capitalize
              ${mode === m ? "bg-brand-500 text-white" : "text-gray-400 hover:text-white"}`}
          >
            {m === "upload" ? "📂 Upload File" : "🎤 Record"}
          </button>
        ))}
      </div>

      {mode === "upload" ? (
        <label className="flex flex-col items-center justify-center w-full h-36 border-2 border-dashed border-surface-border rounded-xl cursor-pointer hover:border-brand-500/50 transition-colors bg-surface-dark group">
          <span className="text-3xl mb-2">🎵</span>
          <span className="text-sm text-gray-400 group-hover:text-gray-300">Click to upload WAV / MP3 / OGG</span>
          {audioBlob && <span className="text-xs text-brand-400 mt-1">✓ File loaded — ready to analyze</span>}
          <input type="file" accept="audio/*" onChange={handleFileChange} className="hidden" />
        </label>
      ) : (
        <div className="rounded-xl bg-surface-dark border border-surface-border p-5">
          {/* Waveform */}
          <div className="flex items-end justify-center gap-0.5 h-16 mb-5">
            {waveData.map((h, i) => (
              <div
                key={i}
                className="w-1.5 rounded-full transition-all duration-75"
                style={{
                  height: `${h}px`,
                  backgroundColor: recording ? "#5a8dee" : "#21262d",
                  opacity: recording ? 0.7 + (i % 3) * 0.1 : 1,
                }}
              />
            ))}
          </div>

          {recording && (
            <div className="text-center text-brand-400 font-mono text-lg mb-4 animate-pulse">
              ⏺ {String(Math.floor(duration / 60)).padStart(2, "0")}:{String(duration % 60).padStart(2, "0")}
            </div>
          )}

          <div className="flex gap-3 justify-center">
            {!recording ? (
              <button
                onClick={startRecording}
                className="px-6 py-2.5 rounded-xl bg-brand-500 hover:bg-brand-600 text-white font-semibold text-sm transition-colors"
              >
                🎤 Start Recording
              </button>
            ) : (
              <button
                onClick={stopRecording}
                className="px-6 py-2.5 rounded-xl bg-red-500 hover:bg-red-600 text-white font-semibold text-sm transition-colors animate-pulse-glow"
              >
                ⏹ Stop Recording
              </button>
            )}
          </div>
        </div>
      )}

      {audioURL && (
        <div className="rounded-xl bg-surface-dark border border-surface-border p-4">
          <p className="text-xs text-gray-400 mb-2">Preview</p>
          <audio controls src={audioURL} className="w-full h-8" />
        </div>
      )}

      {error && (
        <div className="rounded-xl bg-red-500/10 border border-red-500/30 px-4 py-3 text-sm text-red-400">⚠️ {error}</div>
      )}

      <button
        onClick={analyze}
        disabled={loading || !audioBlob || recording}
        className="w-full py-3 rounded-xl bg-brand-500 hover:bg-brand-600 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold transition-colors flex items-center justify-center gap-2"
      >
        {loading ? <><div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> Analyzing…</> : "🎧 Analyze Audio"}
      </button>

      {loading && <Spinner label="Extracting Mel Spectrogram…" />}
      {result && <EmotionResult result={result} />}
    </div>
  );
}
