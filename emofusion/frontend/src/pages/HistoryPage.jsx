import React, { useEffect, useState } from "react";
import {
  Chart as ChartJS,
  CategoryScale, LinearScale, PointElement, LineElement,
  ArcElement, BarElement, Tooltip, Legend, Filler,
} from "chart.js";
import { Line, Doughnut } from "react-chartjs-2";
import Layout from "../components/Layout";
import Spinner from "../components/Spinner";
import api from "../utils/api";
import { getEmotion, formatTime, timeAgo } from "../utils/emotions";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, ArcElement, BarElement, Tooltip, Legend, Filler);

const EMOTIONS = ["happy", "sad", "angry", "fear", "neutral", "disgust", "surprise"];

export default function HistoryPage() {
  const [history, setHistory] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState("all");

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [histRes, profileRes] = await Promise.all([
        api.get("/history?limit=100"),
        api.get("/profile"),
      ]);
      setHistory(histRes.data.history);
      setStats(profileRes.data.stats);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  const filtered = filter === "all" ? history : history.filter((h) => h.input_type === filter);

  // Chart data — last 7 days trend
  const last7 = Array.from({ length: 7 }, (_, i) => {
    const d = new Date();
    d.setDate(d.getDate() - (6 - i));
    return d.toLocaleDateString("en-IN", { weekday: "short" });
  });
  const trendDatasets = EMOTIONS.slice(0, 4).map((emo) => {
    const emoInfo = getEmotion(emo);
    const counts = last7.map((_, dayIdx) => {
      const d = new Date();
      d.setDate(d.getDate() - (6 - dayIdx));
      const dateStr = d.toDateString();
      return history.filter(
        (h) => new Date(h.timestamp).toDateString() === dateStr && h.emotion === emo
      ).length;
    });
    return {
      label: emoInfo.label,
      data: counts,
      borderColor: emoInfo.color,
      backgroundColor: `${emoInfo.color}20`,
      fill: true,
      tension: 0.4,
      pointRadius: 4,
    };
  });

  // Donut chart
  const dist = stats?.emotion_distribution || {};
  const donutData = {
    labels: Object.keys(dist).map((k) => getEmotion(k).label),
    datasets: [{
      data: Object.values(dist),
      backgroundColor: Object.keys(dist).map((k) => getEmotion(k).color + "cc"),
      borderColor: Object.keys(dist).map((k) => getEmotion(k).color),
      borderWidth: 1,
    }],
  };

  const chartOpts = {
    responsive: true,
    plugins: { legend: { labels: { color: "#9ca3af", font: { size: 11 } } } },
    scales: {
      x: { ticks: { color: "#6b7280" }, grid: { color: "#21262d" } },
      y: { ticks: { color: "#6b7280" }, grid: { color: "#21262d" }, beginAtZero: true },
    },
  };

  if (loading) return <Layout><Spinner label="Loading your emotion history…" /></Layout>;

  return (
    <Layout>
      <div className="mb-8">
        <h1 className="font-display font-bold text-2xl md:text-3xl text-white mb-1">Emotion History</h1>
        <p className="text-gray-400 text-sm">Your emotional journey over time.</p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {[
          { label: "Total Analyses", value: stats?.total || 0, icon: "📊" },
          { label: "Dominant Emotion", value: getEmotion(stats?.dominant_emotion)?.label || "—", icon: getEmotion(stats?.dominant_emotion)?.emoji || "🤔" },
          { label: "Text Analyses", value: stats?.by_type?.text || 0, icon: "💬" },
          { label: "Audio / Camera", value: (stats?.by_type?.audio || 0) + (stats?.by_type?.camera || 0), icon: "🎤" },
        ].map((s, i) => (
          <div key={i} className="glass rounded-2xl p-5">
            <div className="text-2xl mb-2">{s.icon}</div>
            <div className="font-display font-bold text-xl text-white">{s.value}</div>
            <div className="text-xs text-gray-400 mt-0.5">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        <div className="lg:col-span-2 glass rounded-2xl p-6">
          <h3 className="font-display font-bold text-white mb-5">7-Day Emotion Trend</h3>
          {history.length > 0 ? (
            <Line data={{ labels: last7, datasets: trendDatasets }} options={chartOpts} />
          ) : (
            <div className="flex items-center justify-center h-40 text-gray-500 text-sm">No data yet</div>
          )}
        </div>
        <div className="glass rounded-2xl p-6">
          <h3 className="font-display font-bold text-white mb-5">Distribution</h3>
          {Object.keys(dist).length > 0 ? (
            <Doughnut data={donutData} options={{ responsive: true, plugins: { legend: { position: "bottom", labels: { color: "#9ca3af", font: { size: 10 } } } } }} />
          ) : (
            <div className="flex items-center justify-center h-40 text-gray-500 text-sm">No data yet</div>
          )}
        </div>
      </div>

      {/* History table */}
      <div className="glass rounded-2xl p-6">
        <div className="flex flex-wrap items-center justify-between gap-4 mb-5">
          <h3 className="font-display font-bold text-white">All Records</h3>
          <div className="flex gap-2">
            {["all", "text", "audio", "camera"].map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`px-3 py-1.5 rounded-lg text-xs font-medium capitalize transition-colors
                  ${filter === f ? "bg-brand-500/20 text-brand-400 border border-brand-500/30" : "text-gray-400 hover:text-white"}`}
              >
                {f === "all" ? "All" : { text: "💬 Text", audio: "🎤 Audio", camera: "📷 Camera" }[f]}
              </button>
            ))}
          </div>
        </div>

        {filtered.length === 0 ? (
          <div className="text-center py-12 text-gray-500">
            <div className="text-4xl mb-3">📭</div>
            <p>No records found. Go to Dashboard and run an analysis!</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-surface-border">
                  {["Emotion", "Confidence", "Type", "Time"].map((h) => (
                    <th key={h} className="pb-3 text-left text-xs text-gray-400 uppercase tracking-wider font-medium pr-4">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-border">
                {filtered.map((row, i) => {
                  const emo = getEmotion(row.emotion);
                  return (
                    <tr key={i} className="hover:bg-white/2 transition-colors">
                      <td className="py-3 pr-4">
                        <div className="flex items-center gap-2">
                          <span>{emo.emoji}</span>
                          <span style={{ color: emo.color }} className="font-medium">{emo.label}</span>
                        </div>
                      </td>
                      <td className="py-3 pr-4">
                        <div className="flex items-center gap-2">
                          <div className="w-16 h-1.5 bg-white/10 rounded-full overflow-hidden">
                            <div className="h-full rounded-full" style={{ width: `${row.confidence}%`, backgroundColor: emo.color }} />
                          </div>
                          <span className="text-gray-400 text-xs">{row.confidence}%</span>
                        </div>
                      </td>
                      <td className="py-3 pr-4">
                        <span className="px-2 py-0.5 rounded-md bg-white/5 text-gray-400 text-xs capitalize">{row.input_type}</span>
                      </td>
                      <td className="py-3 text-gray-500 text-xs">{timeAgo(row.timestamp)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </Layout>
  );
}
