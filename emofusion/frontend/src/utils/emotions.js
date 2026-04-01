export const EMOTIONS = {
  happy:    { emoji: "😊", color: "#f9d71c", label: "Happy" },
  sad:      { emoji: "😢", color: "#7aa2f7", label: "Sad" },
  angry:    { emoji: "😠", color: "#f7768e", label: "Angry" },
  fear:     { emoji: "😨", color: "#bb9af7", label: "Fear" },
  neutral:  { emoji: "😐", color: "#9ece6a", label: "Neutral" },
  disgust:  { emoji: "🤢", color: "#ff9e64", label: "Disgust" },
  surprise: { emoji: "😲", color: "#2ac3de", label: "Surprise" },
};

export const getEmotion = (key) =>
  EMOTIONS[key?.toLowerCase()] || { emoji: "🤔", color: "#7d8590", label: key };

export const formatTime = (isoStr) => {
  const d = new Date(isoStr);
  return d.toLocaleString("en-IN", {
    day: "numeric", month: "short", hour: "2-digit", minute: "2-digit",
  });
};

export const timeAgo = (isoStr) => {
  const diff = (Date.now() - new Date(isoStr)) / 1000;
  if (diff < 60) return "just now";
  if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return `${Math.floor(diff / 86400)}d ago`;
};
