// src/components/uploads/ProgressBar.tsx

"use client";

interface ProgressBarProps {
  progress: number;
  filename: string;
}

export default function ProgressBar({ progress, filename }: ProgressBarProps) {
  return (
    <div className="w-full bg-slate-900 border border-slate-800 rounded-lg p-4 mt-4 animate-in fade-in">
      <div className="flex justify-between items-center mb-2">
        <span className="text-xs font-medium text-slate-300 truncate max-w-[80%]">
          Uploading: {filename}
        </span>
        <span className="text-xs font-mono text-blue-400">{progress}%</span>
      </div>
      <div className="w-full bg-slate-950 rounded-full h-1.5 overflow-hidden border border-slate-800">
        <div
          className="bg-blue-600 h-1.5 rounded-full transition-all duration-300 ease-out"
          style={{ width: `${progress}%` }}
        />
      </div>
    </div>
  );
}