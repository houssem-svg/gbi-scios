"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import {
  UploadCloud,
  FileSpreadsheet,
  Loader2,
  CheckCircle2,
  AlertCircle,
  Trash2,
  Play,
  FileText,
} from "lucide-react";
import { projectService } from "@/lib/projectService";
import { uploadService } from "@/lib/uploadService";
import { parsingService, type BoQItem } from "@/lib/parsingService";
import type { Project } from "@/types/project";
import type { UploadedFile } from "@/types/upload";

const ACCEPTED_EXTS = [".csv", ".xlsx", ".xls"];

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
}

function formatDate(iso: string): string {
  try {
    return new Date(iso).toLocaleString("en-GB", {
      day: "2-digit",
      month: "short",
      hour: "2-digit",
      minute: "2-digit",
    });
  } catch {
    return iso;
  }
}

export default function UploadsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState("");
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [boqItems, setBoqItems] = useState<BoQItem[]>([]);
  const [loadingProjects, setLoadingProjects] = useState(true);
  const [loadingFiles, setLoadingFiles] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [parsingId, setParsingId] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [dragOver, setDragOver] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Load projects
  const loadProjects = useCallback(async () => {
    setLoadingProjects(true);
    try {
      const data = await projectService.getAllProjects({ skip: 0, limit: 100 });
      setProjects(data);
      if (data.length > 0) setSelectedProjectId(data[0].id);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load projects.");
    } finally {
      setLoadingProjects(false);
    }
  }, []);

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  // Load files when project changes
  const loadFiles = useCallback(async (projectId: string) => {
    if (!projectId) return;
    setLoadingFiles(true);
    setError(null);
    try {
      const data = await uploadService.getFilesByProject(projectId, {
        skip: 0,
        limit: 100,
      });
      setFiles(data);
    } catch {
      setFiles([]);
    } finally {
      setLoadingFiles(false);
    }
  }, []);

  useEffect(() => {
    if (selectedProjectId) loadFiles(selectedProjectId);
    else {
      setFiles([]);
      setBoqItems([]);
    }
  }, [selectedProjectId, loadFiles]);

  // Upload + parse handler
  const handleFile = async (file: File) => {
    if (!selectedProjectId) {
      setError("Please select a project first.");
      return;
    }
    const ext = file.name.slice(file.name.lastIndexOf(".")).toLowerCase();
    if (!ACCEPTED_EXTS.includes(ext)) {
      setError(`Unsupported file type: ${ext}. Use CSV or Excel.`);
      return;
    }
    if (file.size > 25 * 1024 * 1024) {
      setError("File exceeds 25 MB limit.");
      return;
    }

    setUploading(true);
    setProgress(0);
    setError(null);
    setSuccess(null);

    try {
      // 1. Upload
      const uploaded = await uploadService.uploadFileWithProgress(
        file,
        selectedProjectId,
        (pct) => setProgress(pct),
      );
      setSuccess(`Uploaded "${uploaded.original_filename}" successfully.`);

      // Refresh file list
      await loadFiles(selectedProjectId);

      // 2. Parse (only Excel/CSV — skip PDF)
      if (uploaded.file_type === "csv" || uploaded.file_type === "excel") {
        setParsingId(uploaded.id);
        const result = await parsingService.parseBoq(uploaded.id);
        setBoqItems(result.items);
        setSuccess(
          `Parsed ${result.parsed_rows} rows from "${uploaded.original_filename}".`,
        );
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload/parse failed.");
    } finally {
      setUploading(false);
      setParsingId(null);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setDragOver(false);
    const file = e.dataTransfer.files?.[0];
    if (file) handleFile(file);
  };

  const handleDelete = async (fileId: string) => {
    if (!confirm("Delete this file? This cannot be undone.")) return;
    try {
      await uploadService.deleteFile(fileId);
      await loadFiles(selectedProjectId);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed.");
    }
  };

  const handleParseExisting = async (fileId: string) => {
    setParsingId(fileId);
    setError(null);
    try {
      const result = await parsingService.parseBoq(fileId);
      setBoqItems(result.items);
      setSuccess(`Parsed ${result.parsed_rows} rows.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Parse failed.");
    } finally {
      setParsingId(null);
    }
  };

  return (
    <div className="max-w-7xl mx-auto animate-in fade-in duration-500 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-lg bg-blue-900/30 border border-blue-800/50 flex items-center justify-center">
          <UploadCloud className="w-5 h-5 text-blue-400" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-slate-100">Upload Center</h1>
          <p className="text-xs text-slate-500">
            Upload your BoQ (Excel/CSV) — the system parses it into line items for compliance scanning.
          </p>
        </div>
      </div>

      {/* Project selector */}
      <div className="flex items-center gap-4 bg-slate-900 border border-slate-800 rounded-lg p-4">
        <label htmlFor="proj" className="text-sm font-medium text-slate-300 whitespace-nowrap">
          Project:
        </label>
        {loadingProjects ? (
          <Loader2 className="w-4 h-4 animate-spin text-slate-500" />
        ) : projects.length === 0 ? (
          <span className="text-sm text-slate-500">No projects available.</span>
        ) : (
          <select
            id="proj"
            value={selectedProjectId}
            onChange={(e) => setSelectedProjectId(e.target.value)}
            className="flex-1 bg-slate-950 border border-slate-700 rounded-md px-3 py-2 text-sm text-slate-200 focus:outline-none focus:border-blue-600"
          >
            {projects.map((p) => (
              <option key={p.id} value={p.id}>
                {p.name} — {p.client}
              </option>
            ))}
          </select>
        )}
      </div>

      {/* Banners */}
      {error && (
        <div className="flex items-start gap-2 p-3 bg-red-950/40 border border-red-900/50 rounded-lg text-xs text-red-400">
          <AlertCircle className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <span>{error}</span>
        </div>
      )}
      {success && (
        <div className="flex items-start gap-2 p-3 bg-emerald-950/30 border border-emerald-900/40 rounded-lg text-xs text-emerald-400">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0 mt-0.5" />
          <span>{success}</span>
        </div>
      )}

      {!selectedProjectId ? (
        <div className="text-center py-16 text-slate-500">
          <UploadCloud className="w-12 h-12 mx-auto mb-4 opacity-30" />
          <p>Select a project to start uploading.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* ── LEFT: Drop zone + upload progress ───────────────────── */}
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-6">
            <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider mb-4">
              Upload BoQ File
            </h2>

            <div
              onDragOver={(e) => {
                e.preventDefault();
                setDragOver(true);
              }}
              onDragLeave={() => setDragOver(false)}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`cursor-pointer border-2 border-dashed rounded-lg p-8 text-center transition-colors ${
                dragOver
                  ? "border-blue-500 bg-blue-950/20"
                  : "border-slate-700 hover:border-slate-600 bg-slate-950"
              }`}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,.xlsx,.xls"
                className="hidden"
                onChange={(e) => {
                  const f = e.target.files?.[0];
                  if (f) handleFile(f);
                  e.target.value = "";
                }}
              />
              {uploading ? (
                <div className="space-y-3">
                  <Loader2 className="w-10 h-10 mx-auto animate-spin text-blue-400" />
                  <p className="text-sm text-slate-300">Uploading… {progress}%</p>
                  <div className="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                    <div
                      className="bg-blue-600 h-full transition-all duration-200"
                      style={{ width: `${progress}%` }}
                    />
                  </div>
                </div>
              ) : (
                <div className="space-y-2">
                  <FileSpreadsheet className="w-10 h-10 mx-auto text-slate-500" />
                  <p className="text-sm text-slate-300 font-medium">
                    Drop your BoQ file here, or click to browse
                  </p>
                  <p className="text-xs text-slate-500">
                    Accepted: .csv, .xlsx, .xls — Max 25 MB
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* ── RIGHT: Uploaded files list ─────────────────────────── */}
          <div className="bg-slate-900 border border-slate-800 rounded-lg p-6">
            <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider mb-4">
              Uploaded Files ({files.length})
            </h2>
            {loadingFiles ? (
              <div className="flex justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin text-slate-500" />
              </div>
            ) : files.length === 0 ? (
              <p className="text-sm text-slate-500 text-center py-8">
                No files uploaded yet.
              </p>
            ) : (
              <ul className="space-y-2 max-h-72 overflow-y-auto pr-1">
                {files.map((f) => (
                  <li
                    key={f.id}
                    className="flex items-center gap-3 p-3 bg-slate-950 border border-slate-800 rounded-md"
                  >
                    <FileText className="w-4 h-4 text-slate-500 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-slate-200 truncate">
                        {f.original_filename}
                      </p>
                      <p className="text-xs text-slate-500">
                        {f.file_type} · {formatDate(f.uploaded_at)}
                      </p>
                    </div>
                    {(f.file_type === "csv" || f.file_type === "excel") && (
                      <button
                        onClick={() => handleParseExisting(f.id)}
                        disabled={parsingId === f.id}
                        title="Parse as BoQ"
                        className="p-1.5 text-blue-400 hover:text-blue-300 hover:bg-slate-800 rounded-md transition-colors disabled:opacity-50"
                      >
                        {parsingId === f.id ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <Play className="w-4 h-4" />
                        )}
                      </button>
                    )}
                    <button
                      onClick={() => handleDelete(f.id)}
                      title="Delete"
                      className="p-1.5 text-slate-400 hover:text-red-400 hover:bg-slate-800 rounded-md transition-colors"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      )}

      {/* ── Parsed BoQ items preview ────────────────────────────── */}
      {boqItems.length > 0 && (
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-6">
          <h2 className="text-sm font-semibold text-slate-200 uppercase tracking-wider mb-4">
            Parsed BoQ Items ({boqItems.length})
          </h2>
          <div className="overflow-x-auto max-h-96">
            <table className="w-full text-sm">
              <thead className="sticky top-0 bg-slate-900">
                <tr className="text-xs text-slate-500 uppercase border-b border-slate-800">
                  <th className="text-left py-2 px-2 font-medium">Item Code</th>
                  <th className="text-left py-2 px-2 font-medium">Description</th>
                  <th className="text-right py-2 px-2 font-medium">Qty</th>
                  <th className="text-right py-2 px-2 font-medium">Unit Price</th>
                  <th className="text-right py-2 px-2 font-medium">Total</th>
                  <th className="text-center py-2 px-2 font-medium">Sourcing</th>
                </tr>
              </thead>
              <tbody>
                {boqItems.map((item) => (
                  <tr
                    key={item.id}
                    className="border-b border-slate-800/50 hover:bg-slate-800/30"
                  >
                    <td className="py-2 px-2 font-mono text-xs text-slate-400">
                      {item.item_code || "—"}
                    </td>
                    <td className="py-2 px-2 text-slate-300 max-w-xs truncate">
                      {item.description || "—"}
                    </td>
                    <td className="py-2 px-2 text-right text-slate-400">
                      {item.quantity}
                    </td>
                    <td className="py-2 px-2 text-right text-slate-400">
                      {new Intl.NumberFormat("en-US", {
                        style: "currency",
                        currency: "SAR",
                        maximumFractionDigits: 0,
                      }).format(item.unit_price)}
                    </td>
                    <td className="py-2 px-2 text-right text-slate-200 font-mono">
                      {new Intl.NumberFormat("en-US", {
                        style: "currency",
                        currency: "SAR",
                        maximumFractionDigits: 0,
                      }).format(item.total_price)}
                    </td>
                    <td className="py-2 px-2 text-center">
                      <span
                        className={`text-[10px] px-2 py-0.5 rounded font-medium ${
                          item.sourcing_type === "imported"
                            ? "bg-red-900/40 text-red-400"
                            : "bg-emerald-900/40 text-emerald-400"
                        }`}
                      >
                        {item.sourcing_type}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
