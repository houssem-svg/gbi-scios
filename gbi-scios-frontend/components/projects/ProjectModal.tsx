"use client";

import { useForm } from "react-hook-form";
import { useEffect } from "react";
import { X, Loader2 } from "lucide-react";
import { Project, ProjectCreateInput } from "@/types/project";

interface ProjectModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: ProjectCreateInput) => Promise<void>;
  project?: Project | null;
}

export default function ProjectModal({ isOpen, onClose, onSubmit, project }: ProjectModalProps) {
  // استخدام any بشكل مرن لدعم الحقول المترجمة القادمة من وإلى الباكيند
  const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<any>();

  useEffect(() => {
    if (project) {
      // قمنا بتهيئة البيانات لتدعم الاسمين (صيغة الواجهة وصيغة الباكيند) لضمان ملء الحقول عند التعديل
      reset({
        name: project.name || project.project_name || "",
        client: project.client || project.client_name || "",
        risk_level: project.risk_level || "Moderate",
        status: project.status || "Planning",
      });
    } else {
      reset({ name: "", client: "", risk_level: "Low", status: "Active" });
    }
  }, [project, reset, isOpen]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-950/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-xl shadow-2xl overflow-hidden relative">
        <div className="absolute top-0 left-0 w-full h-1 bg-blue-600" />
        <div className="flex justify-between items-center px-6 py-4 border-b border-slate-800/60">
          <h3 className="text-base font-semibold text-slate-100">
            {project ? "Modify Corporate Enterprise" : "Provision Security Workspace"}
          </h3>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-200 transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit(onSubmit)} className="p-6 space-y-4">
          <div>
            <label className="block text-xs font-medium text-slate-400 uppercase tracking-wider mb-1.5">Project Nomenclature</label>
            <input
              type="text"
              {...register("name", { required: "Nomenclature execution parameter missing" })}
              className="block w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-blue-500 transition-colors"
              placeholder="Strategic Deployment ID"
            />
            {errors.name && <p className="mt-1 text-xs text-red-400">{String(errors.name?.message || errors.name)}</p>}
          </div>

          <div>
            <label className="block text-xs font-medium text-slate-400 uppercase tracking-wider mb-1.5">Sovereign Client</label>
            <input
              type="text"
              {...register("client", { required: "Client assignment missing" })}
              className="block w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-blue-500 transition-colors"
              placeholder="Authority / Entity Name"
            />
            {errors.client && <p className="mt-1 text-xs text-red-400">{String(errors.client?.message || errors.client)}</p>}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-medium text-slate-400 uppercase tracking-wider mb-1.5">Initial Risk Bounds</label>
              <select
                {...register("risk_level")}
                className="block w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-blue-500 transition-colors"
              >
                <option value="Low">Low</option>
                <option value="Moderate">Moderate</option>
                <option value="High">High</option>
                <option value="Critical">Critical</option>
              </select>
            </div>
            <div>
              <label className="block text-xs font-medium text-slate-400 uppercase tracking-wider mb-1.5">System Status</label>
              <select
                {...register("status")}
                className="block w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded-lg text-sm text-slate-200 focus:outline-none focus:border-blue-500 transition-colors"
              >
                <option value="Active">Active</option>
                <option value="Review">Review</option>
                <option value="Compliant">Compliant</option>
              </select>
            </div>
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-slate-800/60 mt-6">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 text-xs font-medium text-slate-400 hover:text-slate-200 bg-slate-800/40 hover:bg-slate-800 border border-slate-800 rounded-lg transition-all"
            >
              Abort
            </button>
            <button
              type="submit"
              disabled={isSubmitting}
              className="flex items-center gap-2 px-4 py-2 text-xs font-medium text-white bg-blue-600 hover:bg-blue-500 rounded-lg transition-all disabled:opacity-50 shadow-lg shadow-blue-900/20"
            >
              {isSubmitting && <Loader2 className="w-3.5 h-3.5 animate-spin" />}
              {project ? "Commit Delta" : "Execute Injection"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}