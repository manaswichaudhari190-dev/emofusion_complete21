import React, { useState, useEffect, useRef, useCallback } from "react";

const PHASES = [
  { label: "INHALE",  duration: 4, color: "#6d28d9", scale: 1.4, instruction: "Breathe in slowly through your nose" },
  { label: "HOLD",   duration: 4, color: "#7c3aed", scale: 1.4, instruction: "Hold your breath gently"              },
  { label: "EXHALE", duration: 6, color: "#4c1d95", scale: 0.75, instruction: "Breathe out slowly through your mouth" },
];
const TOTAL_CYCLES = 5;

export default function BreathingExercise({ onClose }) {
  const [running, setRunning] = useState(false);
  const [phaseIndex, setPhaseIndex] = useState(0);
  const [phaseTime, setPhaseTime] = useState(PHASES[0].duration);
  const [cycle, setCycle] = useState(0);
  const [done, setDone] = useState(false);
  const tickRef = useRef(null);

  const stop = useCallback(() => {
    clearInterval(tickRef.current);
    setRunning(false);
    setPhaseIndex(0);
    setPhaseTime(PHASES[0].duration);
    setCycle(0);
    setDone(false);
  }, []);

  const start = () => {
    setDone(false);
    setPhaseIndex(0);
    setPhaseTime(PHASES[0].duration);
    setCycle(0);
    setRunning(true);
  };

  useEffect(() => {
    if (!running) { clearInterval(tickRef.current); return; }

    tickRef.current = setInterval(() => {
      setPhaseTime((prev) => {
        if (prev > 1) return prev - 1;

        // Move to next phase
        setPhaseIndex((pi) => {
          const nextPi = (pi + 1) % PHASES.length;
          const completedCycle = nextPi === 0;
          if (completedCycle) {
            setCycle((c) => {
              const newCycle = c + 1;
              if (newCycle >= TOTAL_CYCLES) {
                clearInterval(tickRef.current);
                setRunning(false);
                setDone(true);
              }
              return newCycle;
            });
          }
          setPhaseTime(PHASES[nextPi].duration);
          return nextPi;
        });
        return 0;
      });
    }, 1000);

    return () => clearInterval(tickRef.current);
  }, [running]);

  const phase = PHASES[phaseIndex];
  const progress = running ? ((phase.duration - phaseTime) / phase.duration) : 0;
  const circleSize = 160;
  const radius = 60;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference * (1 - progress);

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4"
      style={{ backgroundColor: "rgba(0,0,0,0.80)", backdropFilter: "blur(8px)" }}>
      <div
        className="relative w-full max-w-sm rounded-2xl overflow-hidden"
        style={{
          background: "linear-gradient(160deg, #1e1b4b, #2e1065, #0f172a)",
          border: "1px solid rgba(139,92,246,0.3)",
          boxShadow: "0 0 80px rgba(109,40,217,0.4)",
          animation: "breatheIn 0.4s ease-out",
        }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 pt-6 pb-2">
          <div>
            <h2 className="text-white font-bold text-lg">🫁 Breathing Exercise</h2>
            <p className="text-purple-300/70 text-xs">4-4-6 calm breathing technique</p>
          </div>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 text-gray-300 hover:text-white transition-all flex items-center justify-center"
          >×</button>
        </div>

        {/* Cycle counter */}
        <div className="flex justify-center gap-2 px-6 py-2">
          {Array.from({ length: TOTAL_CYCLES }).map((_, i) => (
            <div key={i} className={`h-1.5 flex-1 rounded-full transition-all duration-500 ${
              i < cycle ? "bg-purple-400" : i === cycle && running ? "bg-purple-600" : "bg-white/10"
            }`} />
          ))}
        </div>
        <p className="text-center text-xs text-purple-300/60 pb-1">
          {done ? "🎉 All done!" : running ? `Cycle ${cycle + 1} of ${TOTAL_CYCLES}` : "Press Start to begin"}
        </p>

        {/* Breathing Circle */}
        <div className="flex flex-col items-center py-8">
          <div className="relative" style={{ width: circleSize, height: circleSize }}>
            {/* Glow pulse ring */}
            <div
              className="absolute inset-0 rounded-full transition-all"
              style={{
                background: `radial-gradient(circle, ${phase.color}44 0%, transparent 70%)`,
                transform: running ? `scale(${phase.scale})` : "scale(1)",
                transition: `transform ${phase.duration}s ease-in-out`,
              }}
            />
            {/* SVG Progress */}
            <svg className="absolute inset-0 -rotate-90" width={circleSize} height={circleSize}>
              <circle cx={circleSize/2} cy={circleSize/2} r={radius}
                fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="6" />
              <circle cx={circleSize/2} cy={circleSize/2} r={radius}
                fill="none" stroke={phase.color} strokeWidth="6"
                strokeLinecap="round"
                strokeDasharray={circumference}
                strokeDashoffset={strokeDashoffset}
                style={{ transition: "stroke-dashoffset 1s linear, stroke 0.5s ease" }}
              />
            </svg>
            {/* Center text */}
            <div className="absolute inset-0 flex flex-col items-center justify-center">
              <span className="text-white font-bold text-xl tracking-widest">
                {running ? phase.label : done ? "DONE" : "READY"}
              </span>
              {running && (
                <span className="text-purple-300 text-3xl font-mono font-bold">{phaseTime}</span>
              )}
            </div>
          </div>

          {/* Instruction */}
          <p className="mt-4 text-sm text-purple-200/70 text-center px-8 h-5">
            {running ? phase.instruction : done ? "Great job! You completed all 5 cycles 🌟" : ""}
          </p>
        </div>

        {/* Phase guide */}
        <div className="flex justify-center gap-3 px-6 pb-4">
          {PHASES.map((p, i) => (
            <div key={i} className={`flex-1 text-center py-2 rounded-lg transition-all ${
              phaseIndex === i && running ? "bg-purple-500/30 border border-purple-500/50" : "bg-white/5"
            }`}>
              <div className="text-xs font-bold text-white">{p.label}</div>
              <div className="text-xs text-gray-400">{p.duration}s</div>
            </div>
          ))}
        </div>

        {/* Controls */}
        <div className="px-6 pb-6 flex gap-3">
          {!running && !done && (
            <button onClick={start}
              className="flex-1 py-3 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-semibold transition-all shadow-lg hover:shadow-purple-500/30">
              ▶ Start
            </button>
          )}
          {running && (
            <button onClick={stop}
              className="flex-1 py-3 rounded-xl bg-white/10 hover:bg-white/20 text-white font-semibold transition-all">
              ⏹ Stop
            </button>
          )}
          {done && (
            <>
              <button onClick={start}
                className="flex-1 py-3 rounded-xl bg-purple-600 hover:bg-purple-500 text-white font-semibold transition-all">
                🔄 Again
              </button>
              <button onClick={onClose}
                className="flex-1 py-3 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold transition-all">
                💚 Done
              </button>
            </>
          )}
        </div>
      </div>

      <style>{`
        @keyframes breatheIn {
          from { opacity: 0; transform: scale(0.9); }
          to   { opacity: 1; transform: scale(1); }
        }
      `}</style>
    </div>
  );
}
