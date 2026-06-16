"use client";

import { X, Loader2, ShieldAlert } from "lucide-react";
import { useState } from "react";

interface DeleteConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => Promise<void>;
  projectName: string;
}

export default function DeleteConfirmModal({ isOpen, onClose, onConfirm, projectName }: DeleteConfirmModalProps) {
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleConfirm = async () => {
    setLoading(true);
    try {
      await onConfirm();
      onClose();
    } catch (error) {
      // Handled globally or propagated
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="w-full max-w-sm bg-slate-900 border border-slate-800 rounded-xl shadow-2xl overflow-hidden relative">
        <div className="absolute top-0 left-0 w-full h-1 bg-red-600" />
        <div className="p-6">
          <div className="flex items-center gap-3 text-red-500 mb-4">
            <div className="p-2 bg-red-950/50 rounded-lg border border-red-900/30">
              <ShieldAlert className="w-5 h-5" />
            </div>
            <h3 className="text-base font-semibold text-slate-100">Purge Destructive Action</h3>
          </div>
          
          <p className="text-sm text-slate-400 leading-relaxed">
            Confirm termination of workspace <span className="text-slate-200 font-mono font-bold">{projectName}</span>? This action deprecates records cascade-wide.
          </p>

          <div className="flex justify-end gap-3 mt-6 pt-4 border-t border-slate-800/60">
            <button
              onClick={onClose}
              disabled={loading}
              className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-slate-200 bg-slate-800/40 border border-slate-800 rounded-lg transition-all"
            >
              Cancel
            </button>
            <button
              onClick={handleConfirm}
              disabled={loading}
              className="flex items-center gap-2 px-4 py-2 text-xs font-medium text-white bg-red-600 hover:bg-red-500 rounded-lg transition-all disabled:opacity-50 shadow-lg shadow-red-900/20"
            >
              {loading && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              Confirm Deprecation
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}