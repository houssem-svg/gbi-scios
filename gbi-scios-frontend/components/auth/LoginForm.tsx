"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { useAuth } from "@/components/providers/AuthProvider";
import { Mail, Lock, Loader2, ArrowRight } from "lucide-react";
import { LoginFormData } from "@/types/auth";

export default function LoginForm() {
  const { login } = useAuth();
  const [authError, setAuthError] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>();

  const onSubmit = async (data: LoginFormData) => {
    setAuthError(null);
    try {
      await login(data);
    } catch (error: any) {
      setAuthError(error.message || "Invalid corporate credentials.");
    }
  };

  return (
    <div className="w-full max-w-md p-8 rounded-2xl bg-slate-900/60 backdrop-blur-xl border border-slate-800 shadow-2xl relative overflow-hidden">
      <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-blue-600 to-indigo-600" />
      
      <div className="mb-8">
        <h2 className="text-2xl font-semibold text-slate-100 tracking-tight">System Authorization</h2>
        <p className="text-sm text-slate-400 mt-2">Enter your credentials to access the secure workspace.</p>
      </div>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
        <div>
          <label className="block text-xs font-medium text-slate-400 uppercase tracking-wider mb-2">
            Corporate Email
          </label>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Mail className="h-4 w-4 text-slate-500" />
            </div>
            <input
              type="email"
              placeholder="name@gbi-scios.com"
              {...register("email", { 
                required: "Corporate email is required",
                pattern: {
                  value: /^[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}$/i,
                  message: "Invalid email address format"
                }
              })}
              className={`block w-full pl-10 pr-3 py-2.5 bg-slate-950 border ${
                errors.email ? "border-red-500/50 focus:border-red-500" : "border-slate-800 focus:border-blue-500"
              } rounded-lg text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:ring-1 focus:ring-blue-500 transition-colors`}
            />
          </div>
          {errors.email && <p className="mt-1.5 text-xs text-red-400">{errors.email.message}</p>}
        </div>

        <div>
          <div className="flex justify-between items-center mb-2">
            <label className="block text-xs font-medium text-slate-400 uppercase tracking-wider">
              Password
            </label>
            <a href="#" className="text-xs font-medium text-blue-500 hover:text-blue-400 transition-colors">
              Forgot Password?
            </a>
          </div>
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Lock className="h-4 w-4 text-slate-500" />
            </div>
            <input
              type="password"
              placeholder="••••••••"
              {...register("password", { required: "Secure password is required" })}
              className={`block w-full pl-10 pr-3 py-2.5 bg-slate-950 border ${
                errors.password ? "border-red-500/50 focus:border-red-500" : "border-slate-800 focus:border-blue-500"
              } rounded-lg text-sm text-slate-200 placeholder-slate-600 focus:outline-none focus:ring-1 focus:ring-blue-500 transition-colors`}
            />
          </div>
          {errors.password && <p className="mt-1.5 text-xs text-red-400">{errors.password.message}</p>}
        </div>

        {authError && (
          <div className="p-3 rounded-md bg-red-950/30 border border-red-900/50">
            <p className="text-xs font-medium text-red-400 text-center">{authError}</p>
          </div>
        )}

        <button
          type="submit"
          disabled={isSubmitting}
          className="w-full flex items-center justify-center gap-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium py-2.5 px-4 rounded-lg transition-all focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 focus:ring-offset-slate-900 disabled:opacity-70 disabled:cursor-not-allowed mt-6"
        >
          {isSubmitting ? (
            <>
              <Loader2 className="w-4 h-4 animate-spin" />
              Authenticating Terminal...
            </>
          ) : (
            <>
              Secure Login
              <ArrowRight className="w-4 h-4" />
            </>
          )}
        </button>
      </form>
    </div>
  );
}