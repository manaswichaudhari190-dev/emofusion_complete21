import React from "react";

export default function Spinner({ size = "md", label = "Analyzing..." }) {
  const sz = { sm: "w-5 h-5", md: "w-8 h-8", lg: "w-12 h-12" }[size];
  return (
    <div className="flex flex-col items-center gap-3 py-8">
      <div className={`${sz} border-2 border-brand-500 border-t-transparent rounded-full animate-spin`} />
      {label && <p className="text-sm text-gray-400 animate-pulse">{label}</p>}
    </div>
  );
}
