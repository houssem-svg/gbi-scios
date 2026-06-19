// src/app/dashboard/uploads/page.tsx

"use client";

import { useCallback, useEffect, useState } from "react";
import { Folder, Trash2, FileText, CheckCircle2, AlertCircle } from "lucide-react";
import DragDrop from "@/components/uploads/DragDrop";
import ProgressBar from "@/components/uploads/ProgressBar";
import { uploadService } from "@/lib/uploadService";
import { projectService } from "@/lib/projectService";
import { UploadedFile } from "@/types/upload";
import { Project } from "@/types/project";

const formatDate = (iso?: string): string => {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return "—";
  return d.toLocaleString();
};

export default function UploadCenterPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>("");

  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [loadingFiles, setLoadingFiles] = useState(false);

  const [uploadingFile, setUploadingFile] = useState<File | null>(null);
  const [uploadProgress, setUploadProgress] = useState(0);

  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [statusMsg, setStatusMsg] = useState<{ type: "error" | "success"; text: string } | null>(null);

  // FE-15: wrap loader in useCallback so it can be a stable dep of useEffect.
  const fetchProjects = useCallback(async () => {
    try {
      const data = await projectService.getAllProjects({ skip: 0, limit: 100 });
      setProjects(data);
      if (data.length > 0) {
        setSelectedProjectId(data[0].id);
      }
    } catch {
      setStatusMsg({ type: "error", text: "Failed to fetch project scopes." });
    }
  }, []);

  // Initialize Projects
  useEffect(() => {
    fetchProjects();
  }, [fetchProjects]);

  // FE-15: wrap files loader in useCallback; takes projectId as arg so it
  // can be a stable dep of the selectedProjectId effect.
  const fetchFiles = useCallback(async (projectId: string) => {
    setLoadingFiles(true);
    try {
      const data = await uploadService.getFilesByProject(projectId, {
        skip: 0,
        limit: 100,
      });
      setFiles(Array.isArray(data) ? data : []);
    } catch {
      setStatusMsg({ type: "error", text: "Failed to retrieve uploaded files." });
    } finally {
      setLoadingFiles(false);
    }
  }, []);

  // Fetch Files on Project Change
  useEffect(() => {
    if (!selectedProjectId) return;
    fetchFiles(selectedProjectId);
  }, [selectedProjectId, fetchFiles]);

  const handleFileUpload = async (file: File) => {
    if (!selectedProjectId) {
      setStatusMsg({ type: "error", text: "Target project must be selected." });
      return;
    }

    setUploadingFile(file);
    setUploadProgress(0);
    setStatusMsg(null);

    try {
      const newFile = await uploadService.uploadFileWithProgress(file, selectedProjectId, (p) =>
        setUploadProgress(p),
      );
      setFiles((prev) => [newFile, ...prev]);
      setStatusMsg({ type: "success", text: "File uploaded successfully." });
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Upload failed.";
      setStatusMsg({ type: "error", text: msg });
    } finally {
      setTimeout(() => setUploadingFile(null), 600);
    }
  };

  const handleDeleteFile = async (id: string) => {
    setDeletingId(id);
    try {
      await uploadService.deleteFile(id);
      setFiles((prev) => prev.filter((f) => f.id !== id));
      setStatusMsg({ type: "success", text: "File deleted." });
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to delete file.";
      setStatusMsg({ type: "error", text: msg });
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <div className="max-w-5xl mx-auto animate-in fade-in duration-500 space-y-6">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-100 tracking-tight">Upload Center</h1>
        <p className="text-sm text-slate-400 mt-1">
          Ingest and manage compliance evidence documents for each project scope.
        </p>
      </div>

      {statusMsg && (
        <div
          className={`flex items-center gap-2 p-3 text-sm rounded-lg border ${
            statusMsg.type === "error"
              ? "bg-red-950/40 text-red-400 border-red-900/50"
              : "bg-emerald-950/40 text-emerald-400 border-emerald-900/50"
          }`}
        >
          {statusMsg.type === "error" ? (
            <AlertCircle className="w-4 h-4 shrink-0" />
          ) : (
            <CheckCircle2 className="w-4 h-4 shrink-0" />
          )}
          {statusMsg.text}
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left Column: Upload UI */}
        <div className="md:col-span-1 space-y-4">
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl p-5">
            <label className="block text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">
              Target Project
            </label>
            <select
              value={selectedProjectId}
              onChange={(e) => setSelectedProjectId(e.target.value)}
              className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-blue-500 transition-colors mb-4"
              disabled={!!uploadingFile}
            >
              <option value="" disabled>
                Select a project
              </option>
              {projects.map((p) => (
                <option key={p.id} value={p.id}>
                  {p.name}
                </option>
              ))}
            </select>

            <DragDrop onFileSelect={handleFileUpload} disabled={!selectedProjectId || !!uploadingFile} />

            {uploadingFile && (
              <ProgressBar progress={uploadProgress} filename={uploadingFile.name} />
            )}
          </div>
        </div>

        {/* Right Column: Files List */}
        <div className="md:col-span-2">
          <div className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden shadow-xl min-h-[400px] flex flex-col">
            <div className="px-6 py-4 border-b border-slate-800 bg-slate-950/80 flex justify-between items-center">
              <h3 className="text-sm font-semibold text-slate-200 flex items-center gap-2">
                <Folder className="w-4 h-4 text-blue-500/70" />
                Uploaded Files
              </h3>
              <span className="text-xs text-slate-500 bg-slate-900 px-2 py-1 rounded-md border border-slate-800">
                {files.length} {files.length === 1 ? "file" : "files"}
              </span>
            </div>

            <div className="flex-1 overflow-y-auto max-h-[640px] custom-scrollbar">
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
                  <h4 className="text-sm font-medium text-slate-300">No files uploaded yet</h4>
                  <p className="text-xs text-slate-500 mt-1 max-w-xs">
                    Upload a CSV / XLSX / PDF to start building compliance evidence.
                  </p>
                </div>
              ) : (
                <table className="w-full text-left text-sm whitespace-nowrap">
                  <thead className="bg-slate-950/60 text-slate-400 border-b border-slate-800 sticky top-0">
                    <tr>
                      <th className="px-6 py-3 font-medium uppercase tracking-wider text-xs">Filename</th>
                      <th className="px-6 py-3 font-medium uppercase tracking-wider text-xs">Type</th>
                      <th className="px-6 py-3 font-medium uppercase tracking-wider text-xs">Uploaded By</th>
                      <th className="px-6 py-3 font-medium uppercase tracking-wider text-xs">Uploaded At</th>
                      <th className="px-6 py-3 font-medium text-right uppercase tracking-wider text-xs">Action</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/50">
                    {files.map((file) => (
                      <tr key={file.id} className="hover:bg-slate-800/30 transition-colors group">
                        <td className="px-6 py-3">
                          <div className="flex items-center gap-3">
                            <div className="p-2 bg-blue-950/30 text-blue-400 rounded-lg border border-blue-900/30 shrink-0">
                              <FileText className="w-4 h-4" />
                            </div>
                            <span className="text-slate-200 font-medium truncate max-w-[260px]">
                              {file.original_filename || "—"}
                            </span>
                          </div>
                        </td>
                        <td className="px-6 py-3">
                          <span className="px-2 py-0.5 rounded-md text-xs font-mono text-slate-300 bg-slate-950 border border-slate-800">
                            {file.file_type || "—"}
                          </span>
                        </td>
                        <td className="px-6 py-3 text-slate-400 font-mono text-xs">
                          {file.uploaded_by ? file.uploaded_by.slice(0, 8) : "—"}
                        </td>
                        <td className="px-6 py-3 text-slate-400 text-xs">
                          {formatDate(file.uploaded_at)}
                        </td>
                        <td className="px-6 py-3 text-right">
                          <button
                            onClick={() => handleDeleteFile(file.id)}
                            disabled={deletingId === file.id}
                            className="p-2 text-slate-500 hover:text-red-400 hover:bg-red-950/40 rounded-lg transition-all opacity-0 group-hover:opacity-100 focus:opacity-100 disabled:opacity-50 disabled:cursor-not-allowed"
                            title="Delete file"
                          >
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
