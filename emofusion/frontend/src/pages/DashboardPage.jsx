import React, { useState } from "react";
import Layout from "../components/Layout";
import TextDetection from "../components/TextDetection";
import AudioDetection from "../components/AudioDetection";
import CameraDetection from "../components/CameraDetection";
import SuggestionModal from "../components/SuggestionModal";
import CrisisBanner from "../components/CrisisBanner";
import BreathingExercise from "../components/BreathingExercise";
import { useAuth } from "../context/AuthContext";
import { getEmotion, timeAgo } from "../utils/emotions";

const TABS = [
  { key: "text",   label: "Text",   icon: "💬", desc: "NLP emotion detection" },
  { key: "audio",  label: "Audio",  icon: "🎤", desc: "Mel Spectrogram + CNN" },
  { key: "camera", label: "Camera", icon: "📷", desc: "Real-time face analysis" },
];

export default function DashboardPage() {
  const [activeTab, setActiveTab] = useState("text");
  const [recentResults, setRecentResults] = useState([]);
  const [lastResult, setLastResult] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [showBreathing, setShowBreathing] = useState(false);
  const { user } = useAuth();

  const NEGATIVE_EMOTIONS = ["sad", "fear", "angry", "disgust"];

  const handleResult = (data) => {
    setLastResult(data);
    setRecentResults((prev) =>
      [{ ...data, ts: new Date().toISOString() }, ...prev].slice(0, 5)
    );
    // Auto-open modal for negative emotions
    if (NEGATIVE_EMOTIONS.includes(data.emotion?.toLowerCase())) {
      setTimeout(() => setShowModal(true), 600);
    }
  };

  // Pass onResult + modal handlers down to detection components
  const detectionProps = {
    onResult: handleResult,
    onOpenModal: () => setShowModal(true),
    onStartBreathing: () => setShowBreathing(true),
  };

  return (
    <Layout>
      {/* Page header */}
      <div className="mb-8">
        <h1 className="font-display font-bold text-2xl md:text-3xl text-white mb-1">
          Welcome back, {user?.name?.split(" ")[0]} 👋
        </h1>
        <p className="text-gray-400 text-sm">
          Choose a detection mode and analyze your emotions in real-time.
        </p>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
        {/* Main panel */}
        <div className="xl:col-span-2">
          {/* Tab selector */}
          <div className="glass rounded-2xl p-2 flex gap-2 mb-6">
            {TABS.map((t) => (
              <button
                key={t.key}
                onClick={() => setActiveTab(t.key)}
                className={`flex-1 flex flex-col items-center gap-1 py-3 px-2 rounded-xl transition-all text-center
                  ${activeTab === t.key
                    ? "bg-brand-500/20 border border-brand-500/40 text-brand-400"
                    : "text-gray-400 hover:text-white hover:bg-white/5"}`}
              >
                <span className="text-xl">{t.icon}</span>
                <span className="font-semibold text-sm">{t.label}</span>
                <span className="text-xs opacity-60 hidden md:block">{t.desc}</span>
              </button>
            ))}
          </div>

          {/* Detection panel */}
          <div className="glass rounded-2xl p-6">
            <div className="flex items-center gap-3 mb-6 pb-5 border-b border-surface-border">
              <div className="w-10 h-10 rounded-xl bg-brand-500/20 flex items-center justify-center text-xl">
                {TABS.find((t) => t.key === activeTab)?.icon}
              </div>
              <div>
                <h2 className="font-display font-bold text-white">
                  {TABS.find((t) => t.key === activeTab)?.label} Emotion Detection
                </h2>
                <p className="text-xs text-gray-400">
                  {TABS.find((t) => t.key === activeTab)?.desc}
                </p>
              </div>
            </div>

            {activeTab === "text"   && <TextDetection   {...detectionProps} />}
            {activeTab === "audio"  && <AudioDetection  {...detectionProps} />}
            {activeTab === "camera" && <CameraDetection {...detectionProps} />}
          </div>
        </div>

        {/* Right sidebar */}
        <div className="space-y-6">
          {/* Session Summary */}
          <div className="glass rounded-2xl p-5">
            <h3 className="font-display font-bold text-white mb-4">Session Summary</h3>
            <div className="space-y-3">
              {recentResults.length === 0 ? (
                <p className="text-sm text-gray-500 text-center py-4">
                  Run an analysis to see results here
                </p>
              ) : (
                recentResults.map((r, i) => {
                  const emo = getEmotion(r.emotion);
                  return (
                    <div
                      key={i}
                      className="flex items-center gap-3 p-3 rounded-xl bg-white/3 border border-surface-border animate-fade-in"
                    >
                      <span className="text-2xl">{emo.emoji}</span>
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center justify-between">
                          <span className="font-semibold text-sm" style={{ color: emo.color }}>
                            {emo.label}
                          </span>
                          <span className="text-xs text-gray-500">{r.confidence}%</span>
                        </div>
                        <div className="flex items-center justify-between">
                          <span className="text-xs text-gray-500 capitalize">{r.input_type}</span>
                          <span className="text-xs text-gray-600">{timeAgo(r.ts)}</span>
                        </div>
                      </div>
                    </div>
                  );
                })
              )}
            </div>
          </div>

          {/* Mental Health Quick Access */}
          <div className="glass rounded-2xl p-5">
            <h3 className="font-display font-bold text-white mb-3">🧘 Wellness Tools</h3>
            <div className="space-y-2">
              <button
                onClick={() => setShowBreathing(true)}
                className="w-full flex items-center gap-3 p-3 rounded-xl bg-purple-500/10 border border-purple-500/30 hover:bg-purple-500/20 transition-all text-left"
              >
                <span className="text-xl">🫁</span>
                <div>
                  <div className="text-sm font-semibold text-purple-300">Guided Breathing</div>
                  <div className="text-xs text-gray-400">4-4-6 calming technique</div>
                </div>
              </button>
              {lastResult && NEGATIVE_EMOTIONS.includes(lastResult.emotion?.toLowerCase()) && (
                <button
                  onClick={() => setShowModal(true)}
                  className="w-full flex items-center gap-3 p-3 rounded-xl bg-blue-500/10 border border-blue-500/30 hover:bg-blue-500/20 transition-all text-left"
                >
                  <span className="text-xl">💙</span>
                  <div>
                    <div className="text-sm font-semibold text-blue-300">View Suggestions</div>
                    <div className="text-xs text-gray-400">Tips & helpline numbers</div>
                  </div>
                </button>
              )}
            </div>
          </div>

          {/* Tips card */}
          <div className="glass rounded-2xl p-5">
            <h3 className="font-display font-bold text-white mb-3">💡 Tips</h3>
            <ul className="space-y-2.5">
              {[
                { icon: "💬", tip: "Use full sentences for better text analysis." },
                { icon: "🎤", tip: "Record in a quiet environment for accurate audio results." },
                { icon: "📷", tip: "Ensure your face is well-lit for camera detection." },
                { icon: "📊", tip: "Check History to track your emotion trends over time." },
              ].map((item, i) => (
                <li key={i} className="flex gap-2.5 text-xs text-gray-400">
                  <span>{item.icon}</span>
                  <span>{item.tip}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>

      {/* ── Overlays ── */}
      {showModal && lastResult?.suggestion && (
        <SuggestionModal
          emotion={lastResult.emotion}
          suggestion={lastResult.suggestion}
          onClose={() => setShowModal(false)}
          onStartBreathing={() => { setShowModal(false); setShowBreathing(true); }}
        />
      )}

      {showBreathing && (
        <BreathingExercise onClose={() => setShowBreathing(false)} />
      )}

      <CrisisBanner emotion={lastResult?.emotion} />
    </Layout>
  );
}
