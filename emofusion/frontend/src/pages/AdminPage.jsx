import React, { useEffect, useState } from "react";
import Layout from "../components/Layout";
import Spinner from "../components/Spinner";
import api from "../utils/api";
import { getEmotion, timeAgo } from "../utils/emotions";

export default function AdminPage() {
  const [users, setUsers] = useState([]);
  const [logs, setLogs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [activeTab, setActiveTab] = useState("users");

  useEffect(() => { fetchData(); }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [uRes, eRes] = await Promise.all([
        api.get("/admin/users"),
        api.get("/admin/emotions"),
      ]);
      setUsers(uRes.data.users);
      setLogs(eRes.data.logs);
    } catch (e) {
      setError(e.response?.status === 403
        ? "Access denied. Admin privileges required."
        : "Failed to load admin data.");
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <Layout><Spinner label="Loading admin panel…" /></Layout>;

  if (error) return (
    <Layout>
      <div className="flex flex-col items-center justify-center min-h-64 gap-4">
        <div className="text-5xl">🔐</div>
        <p className="text-red-400 text-center">{error}</p>
        <p className="text-gray-500 text-sm">Set <code className="bg-white/5 px-1.5 py-0.5 rounded">is_admin: true</code> in MongoDB for your user document.</p>
      </div>
    </Layout>
  );

  return (
    <Layout>
      <div className="mb-8">
        <h1 className="font-display font-bold text-2xl md:text-3xl text-white mb-1">Admin Panel</h1>
        <p className="text-gray-400 text-sm">Manage users and view all emotion logs.</p>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        {[
          { label: "Total Users", value: users.length, icon: "👥" },
          { label: "Total Logs", value: logs.length, icon: "📋" },
          { label: "Text Logs", value: logs.filter((l) => l.input_type === "text").length, icon: "💬" },
          { label: "Audio + Camera", value: logs.filter((l) => l.input_type !== "text").length, icon: "🎤" },
        ].map((s, i) => (
          <div key={i} className="glass rounded-2xl p-5">
            <div className="text-2xl mb-2">{s.icon}</div>
            <div className="font-display font-bold text-xl text-white">{s.value}</div>
            <div className="text-xs text-gray-400 mt-0.5">{s.label}</div>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-5">
        {["users", "logs"].map((t) => (
          <button
            key={t}
            onClick={() => setActiveTab(t)}
            className={`px-5 py-2 rounded-xl text-sm font-medium capitalize transition-colors
              ${activeTab === t ? "bg-brand-500/20 text-brand-400 border border-brand-500/30" : "text-gray-400 hover:text-white"}`}
          >
            {t === "users" ? "👥 Users" : "📋 Emotion Logs"}
          </button>
        ))}
      </div>

      {/* Users table */}
      {activeTab === "users" && (
        <div className="glass rounded-2xl p-6">
          <h3 className="font-display font-bold text-white mb-5">Registered Users</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-surface-border">
                  {["Name", "Email", "Role", "Joined"].map((h) => (
                    <th key={h} className="pb-3 text-left text-xs text-gray-400 uppercase tracking-wider pr-4">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-border">
                {users.map((u) => (
                  <tr key={u._id} className="hover:bg-white/2 transition-colors">
                    <td className="py-3 pr-4">
                      <div className="flex items-center gap-2">
                        <div className="w-7 h-7 rounded-full bg-brand-500/30 flex items-center justify-center text-xs font-bold text-brand-400">
                          {u.name?.[0]?.toUpperCase()}
                        </div>
                        <span className="text-white font-medium">{u.name}</span>
                      </div>
                    </td>
                    <td className="py-3 pr-4 text-gray-400">{u.email}</td>
                    <td className="py-3 pr-4">
                      <span className={`px-2 py-0.5 rounded-md text-xs ${u.is_admin ? "bg-brand-500/20 text-brand-400" : "bg-white/5 text-gray-400"}`}>
                        {u.is_admin ? "Admin" : "User"}
                      </span>
                    </td>
                    <td className="py-3 text-gray-500 text-xs">{u.created_at ? timeAgo(u.created_at) : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Logs table */}
      {activeTab === "logs" && (
        <div className="glass rounded-2xl p-6">
          <h3 className="font-display font-bold text-white mb-5">All Emotion Logs</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-surface-border">
                  {["Emotion", "Confidence", "Type", "User ID", "Time"].map((h) => (
                    <th key={h} className="pb-3 text-left text-xs text-gray-400 uppercase tracking-wider pr-4">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody className="divide-y divide-surface-border">
                {logs.map((log, i) => {
                  const emo = getEmotion(log.emotion);
                  return (
                    <tr key={i} className="hover:bg-white/2 transition-colors">
                      <td className="py-3 pr-4">
                        <div className="flex items-center gap-2">
                          <span>{emo.emoji}</span>
                          <span style={{ color: emo.color }} className="font-medium">{emo.label}</span>
                        </div>
                      </td>
                      <td className="py-3 pr-4 text-gray-400">{log.confidence}%</td>
                      <td className="py-3 pr-4">
                        <span className="px-2 py-0.5 rounded-md bg-white/5 text-gray-400 text-xs capitalize">{log.input_type}</span>
                      </td>
                      <td className="py-3 pr-4 text-gray-600 text-xs font-mono truncate max-w-28">{log.user_id}</td>
                      <td className="py-3 text-gray-500 text-xs">{timeAgo(log.timestamp)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </Layout>
  );
}
