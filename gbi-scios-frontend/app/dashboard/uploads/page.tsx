// src/app/dashboard/uploads/page.tsx

"use client";

import { useEffect, useState } from "react";
import { Folder, Trash2, FileText, CheckCircle2, AlertCircle } from "lucide-react";
import DragDrop from "@/components/uploads/DragDrop";
import ProgressBar from "@/components/uploads/ProgressBar";
import { uploadService } from "@/lib/uploadService";
import { projectService } from "@/lib/projectService";
import { UploadedFile } from "@/types/upload";
import { Project } from "@/types/project";

export default function UploadCenterPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");
  
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [loadingFiles, setLoadingFiles] = useState(false);
  
  const [uploadingFile, setUploadingFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);
  
  const [statusMsg, setStatusMsg] = useState<{ type: "error" | "success"; text: string } | null>(null);

  // Initialize Projects
  useEffect(() => {
    const fetchProjects = async () => {
      try {
        const data = await projectService.getAllProjects();
        setProjects(data);
        if (data.length > 0) {
          setSelectedProjectId(data[0].id);
        }
      } catch (err: any) {
        setStatusMsg({ type: "error", text: "Failed to fetch project scopes." });
      }
    };
    fetchProjects();
  }, []);

  // Fetch Files on Project Change
  useEffect(() => {
    if (!selectedProjectId) return;
    
    const fetchFiles = async () => {
      setLoadingFiles(true);
      try {
        const data = await uploadService.getFilesByProject(selectedProjectId);
        setFiles(data);
      } catch (err: any) {
        setStatusMsg({ type: "error", text: "Failed to retrieve telemetry files." });
      } finally {
        setLoadingFiles(false);
      }
    };
    
    fetchFiles();
  }, [selectedProjectId]);

  const handleFileUpload = async (file: File) => {
    if (!selectedProjectId) {
      setStatusMsg({ type: "error", text: "Target project scope must be selected." });
      return;
    }

    setUploadingFile(file);
    setUploadProgress(0);
    setStatusMsg(null);

    try {
      const newFile = await uploadService.uploadFileWithProgress(
        file,
        selectedProjectId,
        (progress) => setUploadProgress(progress)
      );
      
      setFiles((prev) => [newFile, ...prev]);
      setStatusMsg({ type: "success", text: "Payload injected successfully." });
    } catch (err: any) {
      setStatusMsg({ type: "error", text: err.message || "Upload stream failed." });
    } finally {
      setTimeout(() => setUploadingFile(null), 1000); // Wait a second before removing progress bar
    }
  };

  const handleDeleteFile = async (id: string) => {
    try {
      await uploadService.deleteFile(id);
      setFiles((prev) => prev.filter((f) => f.id !== id));
      setStatusMsg({ type: "success", text: "Record purged successfully." });
    } catch (err: any) {
      setStatusMsg({ type: "error", text: "Failed to purge record from server." });
    }
  };

  const formatSize = (bytes: number) => {
    if (bytes === 0) return "0 B";
    const k = 1024;
    const sizes = ["B", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + " " + sizes[i];
  };

  return (
    <div className="max-w-5xl mx-auto animate-in fade-in duration-500 space-y-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-100 tracking-tight">Upload Center</h1>
        <p className="text-sm text-slate-400 mt-1">
          Ingest and manage physical evidence documents for compliance bounds.
        </p>
      </div>

      {statusMsg && (
        <div className={`flex items-center gap-2 p-3 text-sm rounded-lg border ${
          statusMsg.type === "error" 
            ? "bg-red-950/40 text-red-400 border-red-900/50" 
            : "bg-emerald-950/40 text-emerald-400 border-emerald-900/50"
        }`}>
          {statusMsg.type === "error" ? <AlertCircle className="w-4 h-4" /> : <CheckCircle2 className="w-4 h-4" />}
          {statusMsg.text}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left Column: Upload UI */}
        <div className="md:col-span-1 space-y-4">
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5">
            <label className="block text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">
              Target Scope
            </label>
            <select
              value={selectedProjectId}
              onChange={(e) => setSelectedProjectId(e.target.value)}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-blue-500 transition-colors mb-4"
              disabled={!!uploadingFile}
            >
              <option value="" disabled>Select System Boundary</option>
              {projects.map((p) => (
                <option key={p.id} value={p.id}>{p.name}</option>
              ))}
            </select>

            <DragDrop 
              onFileSelect={handleFileUpload} 
              disabled={!selectedProjectId || !!uploadingFile} 
            />

            {uploadingFile && (
              <ProgressBar progress={uploadProgress} filename={uploadingFile.name} />
            )}
          </div>
        </div>

        {/* Right Column: Files List */}
        <div className="md:col-span-2">
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden shadow-xl min-h-[400px]">
            <div className="px-6 py-4 border-b border-slate-800 bg-slate-950/80 flex justify-between items-center">
              <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                <Folder className="w-4 h-4 text-blue-500/70" />
                Ingested Artifacts
              </h3>
              <span className="text-xs text-slate-500 bg-slate-900 px-2 py-1 rounded-md border border-slate-800">
                {files.length} records
              </span>
            </div>
            
            <div className="divide-y divide-slate-800/50">
              {loadingFiles ? (
                <div className="p-6 space-y-4">
                  {[...Array(3)].map((_, i) => (
                    <div key={i} className="flex justify-between items-center animate-pulse">
                      <div className="flex gap-3 items-center w-full">
                        <div className="w-8 h-8 bg-slate-800 rounded-lg"></div>
                        <div className="space-y-2 flex-1">
                          <div className="h-3 bg-slate-800 rounded w-1/3"></div>
                          <div className="h-2 bg-slate-800 rounded w-1/4"></div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : files.length === 0 ? (
                <div className="flex flex-col items-center justify-center py-20 text-center px-4">
                  <div className="p-3 bg-slate-900 rounded-xl border border-slate-800 mb-4 text-slate-600">
                    <FileText className="w-6 h-6" />
                  </div>
                  <h4 className="text-sm font-medium text-slate-300">No telemetry bounds allocated</h4>
                  <p className="text-xs text-slate-500 mt-1 max-w-xs">
                    Upload initial payload to establish compliance evidence chain.
                  </p>
                </div>
              ) : (
                files.map((file) => (
                  <div key={file.id} className="p-4 flex items-center justify-between hover:bg-slate-800/30 transition-colors group">
                    <div className="flex items-center gap-3 overflow-hidden">
                      <div className="p-2 bg-blue-950/30 text-blue-400 rounded-lg border border-blue-900/30 shrink-0">
                        <FileText className="w-5 h-5" />
                      </div>
                      <div className="min-w-0">
                        <p className="text-sm font-medium text-slate-200 truncate pr-4">
                          {file.filename}
                        </p>
                        <div className="flex items-center gap-2 mt-0.5">
                          <span className="text-xs text-slate-500 font-mono">
                            {formatSize(file.file_size)}
                          </span>
                          <span className="w-1 h-1 rounded-full bg-slate-700"></span>
                          <span className="text-xs text-slate-500">
                            {new Date(file.created_at).toLocaleDateString()}
                          </span>
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={() => handleDeleteFile(file.id)}
                      className="p-2 text-slate-500 hover:text-red-400 hover:bg-red-950/40 rounded-lg transition-all opacity-0 group-hover:opacity-100 focus:opacity-100"
                      title="Purge artifact"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}