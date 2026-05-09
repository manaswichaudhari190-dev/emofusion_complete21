import React, { useState } from "react";
import api from "../utils/api";
import EmotionResult from "./EmotionResult";
import Spinner from "./Spinner";

const SAMPLES = [
  { label: "😊 Happy", text: "I'm so thrilled about my results today! Everything is going wonderfully!" },
  { label: "😢 Sad",   text: "I feel so alone and hopeless. Nothing ever works out for me." },
  { label: "😠 Angry", text: "This is completely unacceptable! I'm furious about what happened." },
  { label: "😨 Fear",  text: "I'm terrified of what might happen next. The anxiety is overwhelming." },
];

export default function TextDetection({ onResult, onOpenModal, onStartBreathing }) {
  const [text, setText] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");

  const analyze = async () => {
    if (!text.trim()) return setError("Please enter some text.");
    setLoading(true); setError(""); setResult(null);
    try {
      const { data } = await api.post("/predict-text", { text });
      setResult(data);
      onResult?.(data);
    } catch (e) {
      setError(e.response?.data?.error || "Analysis failed. Is the backend running?");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Quick samples */}
      <div>
        <p className="text-xs text-gray-400 uppercase tracking-widest mb-3">Quick samples</p>
        <div className="flex flex-wrap gap-2">
          {SAMPLES.map((s) => (
            <button
              key={s.label}
              onClick={() => { setText(s.text); setResult(null); setError(""); }}
              className="px-3 py-1.5 rounded-lg bg-white/5 border border-surface-border text-xs text-gray-300 hover:border-brand-500/50 hover:text-white transition-colors"
            >
              {s.label}
            </button>
          ))}
        </div>
      </div>

      {/* Textarea */}
      <div className="relative">
        <textarea
          value={text}
          onChange={(e) => { setText(e.target.value); setResult(null); setError(""); }}
          placeholder="Type or paste text here to detect the emotion…"
          maxLength={1000}
          rows={5}
          className="w-full bg-surface-dark border border-surface-border rounded-xl px-4 py-3 text-sm text-white placeholder-gray-500 resize-none focus:outline-none focus:border-brand-500/60 transition-colors"
        />
        <div className="absolute bottom-3 right-4 text-xs text-gray-500">{text.length}/1000</div>
      </div>

      {error && (
        <div className="rounded-xl bg-red-500/10 border border-red-500/30 px-4 py-3 text-sm text-red-400">
          ⚠️ {error}
        </div>
      )}

      <button
        onClick={analyze}
        disabled={loading || !text.trim()}
        className="w-full py-3 rounded-xl bg-brand-500 hover:bg-brand-600 disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold transition-colors flex items-center justify-center gap-2"
      >
        {loading ? <><div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" /> Analyzing…</> : "💬 Analyze Text"}
      </button>

      {loading && <Spinner label="Running NLP model…" />}
      {result && <EmotionResult result={result} onOpenModal={onOpenModal} onStartBreathing={onStartBreathing} />}
    </div>
  );
}
