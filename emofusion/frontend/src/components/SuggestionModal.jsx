import React, { useState, useEffect } from "react";

const NEGATIVE_EMOTIONS = ["sad", "fear", "angry", "disgust"];

const COLOR_MAP = {
  blue:   { bg: "from-blue-900/90 to-blue-800/80",   border: "border-blue-500/50",   btn: "bg-blue-600 hover:bg-blue-500",   tag: "bg-blue-500/20 text-blue-300",   ring: "#3b82f6" },
  purple: { bg: "from-purple-900/90 to-purple-800/80", border: "border-purple-500/50", btn: "bg-purple-600 hover:bg-purple-500", tag: "bg-purple-500/20 text-purple-300", ring: "#a855f7" },
  red:    { bg: "from-red-900/90 to-red-800/80",     border: "border-red-500/50",     btn: "bg-red-600 hover:bg-red-500",     tag: "bg-red-500/20 text-red-300",     ring: "#ef4444" },
  green:  { bg: "from-green-900/90 to-green-800/80", border: "border-green-500/50",   btn: "bg-green-600 hover:bg-green-500", tag: "bg-green-500/20 text-green-300", ring: "#22c55e" },
  yellow: { bg: "from-yellow-900/90 to-yellow-800/80", border: "border-yellow-500/50", btn: "bg-yellow-600 hover:bg-yellow-500", tag: "bg-yellow-500/20 text-yellow-300", ring: "#eab308" },
  gray:   { bg: "from-gray-900/90 to-gray-800/80",   border: "border-gray-500/50",   btn: "bg-gray-600 hover:bg-gray-500",   tag: "bg-gray-500/20 text-gray-300",   ring: "#6b7280" },
  orange: { bg: "from-orange-900/90 to-orange-800/80", border: "border-orange-500/50", btn: "bg-orange-600 hover:bg-orange-500", tag: "bg-orange-500/20 text-orange-300", ring: "#f97316" },
};

export default function SuggestionModal({ emotion, suggestion, onClose, onStartBreathing }) {
  const [checked, setChecked] = useState({});
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    const isNegative = NEGATIVE_EMOTIONS.includes(emotion?.toLowerCase());
    if (isNegative && suggestion) {
      setTimeout(() => setVisible(true), 100);
    }
    setChecked({});
  }, [emotion, suggestion]);

  const handleClose = () => {
    setVisible(false);
    setTimeout(onClose, 300);
  };

  if (!visible || !suggestion) return null;

  const color = COLOR_MAP[suggestion.color] || COLOR_MAP.gray;
  const toggleCheck = (i) => setChecked((prev) => ({ ...prev, [i]: !prev[i] }));

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ backgroundColor: "rgba(0,0,0,0.75)", backdropFilter: "blur(6px)" }}
      onClick={(e) => e.target === e.currentTarget && handleClose()}
    >
      <div
        className={`relative w-full max-w-lg max-h-[90vh] overflow-y-auto rounded-2xl border ${color.border} bg-gradient-to-b ${color.bg} shadow-2xl`}
        style={{
          animation: "modalIn 0.3s cubic-bezier(0.34,1.56,0.64,1) forwards",
          boxShadow: `0 0 60px ${color.ring}33`,
        }}
      >
        {/* Header */}
        <div className={`sticky top-0 z-10 bg-gradient-to-b ${color.bg} rounded-t-2xl px-6 pt-6 pb-4 border-b ${color.border}`}>
          <button
            onClick={handleClose}
            className="absolute top-4 right-4 w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-gray-300 hover:text-white transition-all text-lg"
          >
            ×
          </button>
          <div className="flex items-center gap-4 pr-8">
            <div className="text-5xl animate-pulse">{suggestion.emoji}</div>
            <div>
              <h2 className="text-xl font-bold text-white leading-tight">{suggestion.title}</h2>
              <p className="text-sm text-gray-300 mt-1">{suggestion.message}</p>
            </div>
          </div>
        </div>

        <div className="px-6 py-5 space-y-6">
          {/* Breathing Exercise CTA */}
          {["sad", "fear"].includes(emotion?.toLowerCase()) && (
            <button
              onClick={() => { handleClose(); onStartBreathing?.(); }}
              className="w-full flex items-center gap-3 p-4 rounded-xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all group"
            >
              <div className="w-10 h-10 rounded-full flex items-center justify-center text-xl"
                style={{ background: `${color.ring}33` }}>
                🫁
              </div>
              <div className="text-left">
                <div className="text-sm font-semibold text-white">Try Guided Breathing</div>
                <div className="text-xs text-gray-400">4-4-6 breathing exercise — calms your nervous system</div>
              </div>
              <div className="ml-auto text-gray-400 group-hover:text-white transition-colors">→</div>
            </button>
          )}

          {/* Tips Checklist */}
          <div>
            <div className="text-xs text-gray-400 uppercase tracking-widest mb-3">✅ Wellness Tips — Check off as you go</div>
            <div className="space-y-2">
              {suggestion.tips.map((tip, i) => (
                <button
                  key={i}
                  onClick={() => toggleCheck(i)}
                  className={`w-full flex items-start gap-3 p-3 rounded-xl border text-left transition-all ${
                    checked[i]
                      ? `border-opacity-50 ${color.border} ${color.tag} opacity-60`
                      : "border-white/10 bg-white/5 hover:bg-white/10"
                  }`}
                >
                  <div className={`mt-0.5 w-5 h-5 flex-shrink-0 rounded border-2 flex items-center justify-center transition-all ${
                    checked[i] ? `border-current bg-current` : "border-gray-500"
                  }`}>
                    {checked[i] && <span className="text-white text-xs font-bold">✓</span>}
                  </div>
                  <span className={`text-sm ${checked[i] ? "line-through text-gray-500" : "text-gray-200"}`}>{tip}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Helplines */}
          {suggestion.helplines?.length > 0 && (
            <div>
              <div className="text-xs text-gray-400 uppercase tracking-widest mb-3">📞 Need to talk to someone?</div>
              <div className="grid grid-cols-1 gap-2">
                {suggestion.helplines.map((h, i) => (
                  <a
                    key={i}
                    href={`tel:${h.number}`}
                    className={`flex items-center justify-between p-3 rounded-xl border ${color.border} ${color.tag} hover:opacity-90 transition-opacity`}
                  >
                    <div className="flex items-center gap-3">
                      <span className="text-lg">📱</span>
                      <span className="text-sm font-semibold">{h.name}</span>
                    </div>
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-mono">{h.number}</span>
                      <span className="text-xs px-2 py-0.5 rounded-full bg-white/10">Call</span>
                    </div>
                  </a>
                ))}
              </div>
            </div>
          )}

          {/* Affirmation */}
          <div className={`rounded-xl p-4 border ${color.border} bg-white/5 text-center`}>
            <div className="text-xs text-gray-400 uppercase tracking-widest mb-2">💫 Affirmation</div>
            <p className="text-base font-semibold text-white italic">"{suggestion.affirmation}"</p>
          </div>
        </div>

        {/* Footer */}
        <div className={`sticky bottom-0 px-6 pb-6 pt-3 bg-gradient-to-t from-black/40 to-transparent`}>
          <button
            onClick={handleClose}
            className="w-full py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold transition-all shadow-lg hover:shadow-emerald-500/30 flex items-center justify-center gap-2"
          >
            💚 I feel better now
          </button>
        </div>
      </div>

      <style>{`
        @keyframes modalIn {
          from { opacity: 0; transform: scale(0.85) translateY(20px); }
          to   { opacity: 1; transform: scale(1) translateY(0); }
        }
      `}</style>
    </div>
  );
}
