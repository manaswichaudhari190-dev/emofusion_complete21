import React, { useState } from "react";
import { getEmotion } from "../utils/emotions";

const NEGATIVE_EMOTIONS = ["sad", "fear", "angry", "disgust"];
const COLOR_MAP = {
  blue:   { border: "border-blue-500/40",   bg: "bg-blue-500/10",   text: "text-blue-300",   pill: "bg-blue-500/20",   ring: "#3b82f6" },
  purple: { border: "border-purple-500/40", bg: "bg-purple-500/10", text: "text-purple-300", pill: "bg-purple-500/20", ring: "#a855f7" },
  red:    { border: "border-red-500/40",     bg: "bg-red-500/10",    text: "text-red-300",    pill: "bg-red-500/20",    ring: "#ef4444" },
  green:  { border: "border-green-500/40",  bg: "bg-green-500/10",  text: "text-green-300",  pill: "bg-green-500/20",  ring: "#22c55e" },
  yellow: { border: "border-yellow-500/40", bg: "bg-yellow-500/10", text: "text-yellow-300", pill: "bg-yellow-500/20", ring: "#eab308" },
  gray:   { border: "border-gray-500/40",   bg: "bg-gray-500/10",   text: "text-gray-300",   pill: "bg-gray-500/20",   ring: "#6b7280" },
  orange: { border: "border-orange-500/40", bg: "bg-orange-500/10", text: "text-orange-300", pill: "bg-orange-500/20", ring: "#f97316" },
};

export default function EmotionResult({ result, onOpenModal, onStartBreathing }) {
  const [showAllTips, setShowAllTips] = useState(false);

  if (!result) return null;
  const { emotion, confidence, breakdown, suggestion, input_type } = result;
  const emo = getEmotion(emotion);
  const inputLabel = { text: "Text", audio: "Audio", camera: "Camera" }[input_type] || input_type;
  const isNegative = NEGATIVE_EMOTIONS.includes(emotion?.toLowerCase());
  const c = COLOR_MAP[suggestion?.color] || COLOR_MAP.gray;
  const visibleTips = showAllTips ? suggestion?.tips : suggestion?.tips?.slice(0, 3);

  return (
    <div className="space-y-4 animate-slide-up">
      {/* Emotion Header Card */}
      <div className={`rounded-2xl border-2 p-6 bg-emotion-${emotion}`}>
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-4">
            <div className="text-6xl">{emo.emoji}</div>
            <div>
              <div className="text-xs text-gray-400 uppercase tracking-widest mb-1">Detected Emotion</div>
              <div className="font-display font-bold text-3xl" style={{ color: emo.color }}>{emo.label}</div>
              <div className="text-sm text-gray-400 mt-1">from {inputLabel}</div>
            </div>
          </div>
          <div className="text-right">
            <div className="text-xs text-gray-400 mb-1">Confidence</div>
            <div className="font-display font-bold text-4xl" style={{ color: emo.color }}>{confidence}%</div>
          </div>
        </div>

        {/* Breakdown bars */}
        {breakdown && (
          <div className="mb-2">
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
                        <div className="h-full rounded-full transition-all duration-700"
                          style={{ width: `${pct}%`, backgroundColor: e.color, opacity: 0.85 }} />
                      </div>
                      <div className="w-10 text-xs text-gray-400">{pct}%</div>
                    </div>
                  );
                })}
            </div>
          </div>
        )}
      </div>

      {/* Suggestion Card */}
      {suggestion && (
        <div className={`rounded-2xl border ${c.border} ${c.bg} overflow-hidden`}
          style={{ boxShadow: `0 0 30px ${c.ring}22` }}>

          {/* Card Header */}
          <div className={`flex items-center justify-between px-5 py-4 border-b ${c.border} bg-black/20`}>
            <div className="flex items-center gap-3">
              <span className="text-3xl">{suggestion.emoji}</span>
              <div>
                <div className={`font-bold text-sm ${c.text}`}>{suggestion.title}</div>
                <div className="text-xs text-gray-400">{suggestion.message}</div>
              </div>
            </div>
            {isNegative && (
              <button
                onClick={onOpenModal}
                className={`text-xs px-3 py-1.5 rounded-lg ${c.pill} ${c.text} hover:opacity-80 transition-opacity font-semibold border ${c.border} flex-shrink-0`}
              >
                View All →
              </button>
            )}
          </div>

          {/* Breathing CTA for sad/fear */}
          {["sad", "fear"].includes(emotion?.toLowerCase()) && (
            <div className="px-5 pt-4">
              <button
                onClick={onStartBreathing}
                className={`w-full flex items-center gap-3 p-3 rounded-xl border ${c.border} bg-white/5 hover:bg-white/10 transition-all`}
              >
                <div className="text-2xl">🫁</div>
                <div className="text-left">
                  <div className={`text-sm font-semibold ${c.text}`}>Try Guided Breathing</div>
                  <div className="text-xs text-gray-400">4-4-6 breathing · calms your nervous system</div>
                </div>
                <div className="ml-auto text-gray-400">▶</div>
              </button>
            </div>
          )}

          {/* Tips */}
          <div className="px-5 py-4">
            <div className="text-xs text-gray-400 uppercase tracking-widest mb-3">
              {isNegative ? "💡 Helpful Tips" : "⭐ Keep the good vibes going"}
            </div>
            <div className="space-y-2">
              {visibleTips?.map((tip, i) => (
                <div key={i} className="flex items-start gap-2 text-sm text-gray-200">
                  <span className={`mt-0.5 text-xs ${c.text}`}>▸</span>
                  <span>{tip}</span>
                </div>
              ))}
            </div>
            {suggestion.tips?.length > 3 && (
              <button
                onClick={() => setShowAllTips((s) => !s)}
                className={`mt-3 text-xs ${c.text} hover:opacity-80 transition-opacity`}
              >
                {showAllTips ? "▲ Show less" : `▼ ${suggestion.tips.length - 3} more tips`}
              </button>
            )}
          </div>

          {/* Helplines — only for negative emotions */}
          {isNegative && suggestion.helplines?.length > 0 && (
            <div className={`px-5 py-4 border-t ${c.border} bg-black/20`}>
              <div className="text-xs text-gray-400 uppercase tracking-widest mb-3">📞 Need to talk to someone?</div>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                {suggestion.helplines.map((h, i) => (
                  <a key={i} href={`tel:${h.number}`}
                    className={`flex items-center gap-2 px-3 py-2 rounded-lg border ${c.border} ${c.pill} hover:opacity-80 transition-opacity`}>
                    <span className="text-base">📱</span>
                    <div className="min-w-0">
                      <div className={`text-xs font-semibold ${c.text} truncate`}>{h.name}</div>
                      <div className="text-xs text-gray-300 font-mono">{h.number}</div>
                    </div>
                  </a>
                ))}
              </div>
            </div>
          )}

          {/* Affirmation */}
          <div className={`px-5 py-4 border-t ${c.border} text-center`}>
            <div className="text-xs text-gray-500 mb-1">💫</div>
            <p className={`text-sm italic font-medium ${c.text}`}>"{suggestion.affirmation}"</p>
          </div>
        </div>
      )}
    </div>
  );
}
