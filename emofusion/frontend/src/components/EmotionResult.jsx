import React from "react";
import { getEmotion } from "../utils/emotions";

export default function EmotionResult({ result }) {
  if (!result) return null;
  const { emotion, confidence, breakdown, suggestion, input_type } = result;
  const emo = getEmotion(emotion);

  const inputLabel = { text: "Text", audio: "Audio", camera: "Camera" }[input_type] || input_type;

  return (
    <div className={`animate-slide-up rounded-2xl border-2 p-6 bg-emotion-${emotion}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <div className="text-6xl">{emo.emoji}</div>
          <div>
            <div className="text-xs text-gray-400 uppercase tracking-widest mb-1">Detected Emotion</div>
            <div
              className="font-display font-bold text-3xl"
              style={{ color: emo.color }}
            >
              {emo.label}
            </div>
            <div className="text-sm text-gray-400 mt-1">from {inputLabel}</div>
          </div>
        </div>
        <div className="text-right">
          <div className="text-xs text-gray-400 mb-1">Confidence</div>
          <div
            className="font-display font-bold text-4xl"
            style={{ color: emo.color }}
          >
            {confidence}%
          </div>
        </div>
      </div>

      {/* Breakdown bars */}
      {breakdown && (
        <div className="mb-6">
          <div className="text-xs text-gray-400 uppercase tracking-widest mb-3">Emotion Breakdown</div>
          <div className="space-y-2">
            {Object.entries(breakdown)
              .sort(([, a], [, b]) => b - a)
              .map(([emo_key, pct]) => {
                const e = getEmotion(emo_key);
                return (
                  <div key={emo_key} className="flex items-center gap-3">
                    <div className="w-16 text-xs text-gray-400 text-right">{e.label}</div>
                    <div className="flex-1 h-2 bg-white/10 rounded-full overflow-hidden">
                      <div
                        className="h-full rounded-full transition-all duration-700"
                        style={{
                          width: `${pct}%`,
                          backgroundColor: e.color,
                          opacity: 0.85,
                        }}
                      />
                    </div>
                    <div className="w-10 text-xs text-gray-400">{pct}%</div>
                  </div>
                );
              })}
          </div>
        </div>
      )}

      {/* Suggestion */}
      {suggestion && (
        <div className="rounded-xl bg-white/5 border border-white/10 p-4">
          <div className="text-xs text-gray-400 uppercase tracking-widest mb-2">💡 Wellness Suggestion</div>
          <p className="text-sm text-gray-200 leading-relaxed">{suggestion}</p>
        </div>
      )}
    </div>
  );
}
