// src/components/uploads/DragDrop.tsx

"use client";

import { useState, useRef } from "react";
import { UploadCloud, FileWarning } from "lucide-react";
import { ALLOWED_FILE_TYPES, MAX_FILE_SIZE } from "@/types/upload";

interface DragDropProps {
  onFileSelect: (file: File) => void;
  disabled?: boolean;
}

export default function DragDrop({ onFileSelect, disabled }: DragDropProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateAndSelect = (file: File) => {
    setError(null);
    if (!ALLOWED_FILE_TYPES.includes(file.type) && !file.name.match(/\.(csv|xlsx|pdf)$/i)) {
      setError("Invalid file type. Supported formats: CSV, XLSX, PDF.");
      return;
    }
    if (file.size > MAX_FILE_SIZE) {
      setError("File exceeds 50MB payload limit.");
      return;
    }
    onFileSelect(file);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (!disabled) setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (disabled) return;

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      validateAndSelect(e.dataTransfer.files[0]);
      e.dataTransfer.clearData();
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      validateAndSelect(e.target.files[0]);
    }
    // Reset input so same file can be selected again if needed
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  return (
    <div className="space-y-3">
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => !disabled && fileInputRef.current?.click()}
        className={`relative border-2 border-dashed rounded-xl p-10 flex flex-col items-center justify-center text-center transition-all ${
          disabled
            ? "border-slate-800 bg-slate-900/20 cursor-not-allowed opacity-50"
            : isDragging
            ? "border-blue-500 bg-blue-950/20 cursor-copy"
            : "border-slate-700 hover:border-slate-500 hover:bg-slate-800/30 cursor-pointer"
        }`}
      >
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleChange}
          accept=".csv,.xlsx,.pdf"
          className="hidden"
          disabled={disabled}
        />
        <div className={`p-4 rounded-full mb-3 ${isDragging ? "bg-blue-900/50" : "bg-slate-800"}`}>
          <UploadCloud className={`w-8 h-8 ${isDragging ? "text-blue-400" : "text-slate-400"}`} />
        </div>
        <h3 className="text-sm font-semibold text-slate-200 mb-1">
          {isDragging ? "Release to Inject Payload" : "Select or Drag Payload"}
        </h3>
        <p className="text-xs text-slate-500 max-w-xs">
          Secure dropzone for CSV, XLSX, and PDF bounds. Max throughput 50MB.
        </p>
      </div>

      {error && (
        <div className="flex items-center gap-2 p-3 text-xs text-red-400 bg-red-950/40 border border-red-900/50 rounded-lg">
          <FileWarning className="w-4 h-4" />
          {error}
        </div>
      )}
    </div>
  );
}