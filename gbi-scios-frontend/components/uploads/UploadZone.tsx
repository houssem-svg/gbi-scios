// src/components/uploads/UploadZone.tsx
"use client";

import { useState, useCallback } from "react";
import { UploadCloud, FileText, X, CheckCircle2, AlertCircle, Loader2 } from "lucide-react";

type UploadFile = {
  id: string;
  name: string;
  size: number;
  progress: number;
  status: "uploading" | "success" | "error";
};

export default function UploadZone() {
  const [isDragging, setIsDragging] = useState(false);
  const [files, setFiles] = useState<UploadFile[]>([]);
  const [selectedProject, setSelectedProject] = useState("");

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const simulateUpload = (newFile: UploadFile) => {
    setFiles((prev) => [newFile, ...prev]);
    
    let progress = 0;
    const interval = setInterval(() => {
      progress += Math.random() * 15;
      if (progress >= 100) {
        progress = 100;
        clearInterval(interval);
        setFiles((prev) =>
          prev.map((f) => (f.id === newFile.id ? { ...f, progress, status: "success" } : f))
        );
      } else {
        setFiles((prev) =>
          prev.map((f) => (f.id === newFile.id ? { ...f, progress } : f))
        );
      }
    }, 300);
  };

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    
    if (!selectedProject) {
      alert("Please select a project first.");
      return;
    }

    const droppedFiles = Array.from(e.dataTransfer.files);
    droppedFiles.forEach((file) => {
      simulateUpload({
        id: Math.random().toString(36).substr(2, 9),
        name: file.name,
        size: file.size,
        progress: 0,
        status: "uploading",
      });
    });
  }, [selectedProject]);

  const removeFile = (id: string) => {
    setFiles((prev) => prev.filter((f) => f.id !== id));
  };

  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-6 shadow-xl mb-6">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h2 className="text-lg font-semibold text-slate-100">Upload Workspace</h2>
          <p className="text-sm text-slate-400">Drag and drop BoQ (XLSX, CSV) or Compliance docs (PDF).</p>
        </div>
        <select 
          value={selectedProject}
          onChange={(e) => setSelectedProject(e.target.value)}
          className="bg-slate-950 border border-slate-800 text-slate-200 text-sm rounded-lg focus:ring-blue-500 focus:border-blue-500 block p-2.5"
        >
          <option value="">Select Target Project...</option>
          <option value="PRJ-092">PRJ-092: GBI-SCIOS Alpha</option>
          <option value="PRJ-093">PRJ-093: Riyadh Metro</option>
        </select>
      </div>

      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-xl p-10 flex flex-col items-center justify-center transition-colors ${
          isDragging ? "border-blue-500 bg-blue-500/10" : "border-slate-700 bg-slate-950/50 hover:bg-slate-800/50 hover:border-slate-600"
        }`}
      >
        <div className="p-4 bg-slate-800 rounded-full mb-4 shadow-inner">
          <UploadCloud className={`w-8 h-8 ${isDragging ? "text-blue-400" : "text-slate-400"}`} />
        </div>
        <p className="text-slate-200 font-medium mb-1">Click to browse or drag files here</p>
        <p className="text-xs text-slate-500">Supported formats: CSV, XLSX, PDF (Max 50MB)</p>
      </div>

      {files.length > 0 && (
        <div className="mt-6 space-y-3">
          <h3 className="text-sm font-semibold text-slate-300 uppercase tracking-wider mb-3">Processing Queue</h3>
          {files.map((file) => (
            <div key={file.id} className="bg-slate-950 border border-slate-800 rounded-lg p-4 relative overflow-hidden">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-3">
                  <FileText className="w-5 h-5 text-blue-500" />
                  <div>
                    <p className="text-sm font-medium text-slate-200 truncate w-48 md:w-64">{file.name}</p>
                    <p className="text-xs text-slate-500">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  {file.status === "uploading" && <Loader2 className="w-4 h-4 text-blue-400 animate-spin" />}
                  {file.status === "success" && <CheckCircle2 className="w-4 h-4 text-emerald-500" />}
                  {file.status === "error" && <AlertCircle className="w-4 h-4 text-red-500" />}
                  <button onClick={() => removeFile(file.id)} className="text-slate-500 hover:text-slate-300">
                    <X className="w-4 h-4" />
                  </button>
                </div>
              </div>
              
              {/* Progress Bar */}
              <div className="w-full bg-slate-800 rounded-full h-1.5 mt-2 overflow-hidden">
                <div 
                  className={`h-1.5 rounded-full transition-all duration-300 ${
                    file.status === "error" ? "bg-red-500" : file.status === "success" ? "bg-emerald-500" : "bg-blue-500"
                  }`}
                  style={{ width: `${file.progress}%` }}
                />
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}