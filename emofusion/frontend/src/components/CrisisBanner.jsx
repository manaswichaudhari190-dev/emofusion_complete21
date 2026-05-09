import React, { useState, useEffect, useRef } from "react";

const CRISIS_EMOTIONS = ["sad", "fear"];

export default function CrisisBanner({ emotion }) {
  const [visible, setVisible] = useState(false);
  const [dismissed, setDismissed] = useState(false);
  const [countdown, setCountdown] = useState(30);
  const timerRef = useRef(null);
  const countdownRef = useRef(null);

  useEffect(() => {
    if (CRISIS_EMOTIONS.includes(emotion?.toLowerCase())) {
      setDismissed(false);
      setVisible(true);
      setCountdown(30);

      // Auto-dismiss after 30 seconds
      clearTimeout(timerRef.current);
      clearInterval(countdownRef.current);

      timerRef.current = setTimeout(() => setVisible(false), 30000);
      countdownRef.current = setInterval(() => {
        setCountdown((c) => {
          if (c <= 1) { clearInterval(countdownRef.current); return 0; }
          return c - 1;
        });
      }, 1000);
    } else {
      setVisible(false);
    }
    return () => {
      clearTimeout(timerRef.current);
      clearInterval(countdownRef.current);
    };
  }, [emotion]);

  const dismiss = () => {
    setVisible(false);
    setDismissed(true);
    clearTimeout(timerRef.current);
    clearInterval(countdownRef.current);
  };

  if (!visible || dismissed) return null;

  return (
    <div
      className="fixed bottom-0 left-0 right-0 z-40"
      style={{
        animation: "slideUp 0.4s ease-out",
        background: emotion?.toLowerCase() === "fear"
          ? "linear-gradient(135deg, #4c1d95, #6d28d9, #7c3aed)"
          : "linear-gradient(135deg, #1e3a5f, #1d4ed8, #2563eb)",
        boxShadow: "0 -4px 30px rgba(0,0,0,0.5)",
      }}
    >
      <div className="max-w-5xl mx-auto px-4 py-3 flex flex-col sm:flex-row items-center gap-3">
        {/* Icon + Text */}
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <span className="text-2xl flex-shrink-0 animate-pulse">
            {emotion?.toLowerCase() === "fear" ? "💜" : "💙"}
          </span>
          <div className="text-sm text-white min-w-0">
            <span className="font-bold">Feeling overwhelmed? You are not alone.</span>
            <span className="hidden sm:inline text-white/80">
              {" "}Free, confidential support is available right now.
            </span>
          </div>
        </div>

        {/* Helpline Buttons */}
        <div className="flex items-center gap-2 flex-wrap justify-center">
          <a
            href="tel:9152987821"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/20 hover:bg-white/30 text-white text-xs font-semibold transition-all border border-white/20"
          >
            📞 iCall: 9152987821
          </a>
          <a
            href="tel:18602662345"
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/20 hover:bg-white/30 text-white text-xs font-semibold transition-all border border-white/20"
          >
            📞 Vandrevala: 1860-2662-345
          </a>
        </div>

        {/* Countdown + Dismiss */}
        <div className="flex items-center gap-2 flex-shrink-0">
          <span className="text-xs text-white/50">{countdown}s</span>
          <button
            onClick={dismiss}
            className="w-7 h-7 rounded-full bg-white/20 hover:bg-white/30 flex items-center justify-center text-white text-sm transition-all"
            title="Dismiss"
          >
            ×
          </button>
        </div>
      </div>

      <style>{`
        @keyframes slideUp {
          from { transform: translateY(100%); opacity: 0; }
          to   { transform: translateY(0); opacity: 1; }
        }
      `}</style>
    </div>
  );
}
