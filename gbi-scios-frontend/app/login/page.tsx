import LoginForm from "@/components/auth/LoginForm";
import { Shield } from "lucide-react";

export default function LoginPage() {
  return (
    <div className="min-h-screen bg-slate-950 flex flex-col justify-center items-center relative overflow-hidden selection:bg-blue-500/30">
      
      {/* Background Decorative Elements */}
      <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] rounded-full bg-blue-900/10 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] rounded-full bg-indigo-900/10 blur-[120px] pointer-events-none" />
      
      {/* Grid Pattern */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#80808012_1px,transparent_1px),linear-gradient(to_bottom,#80808012_1px,transparent_1px)] bg-[size:24px_24px] pointer-events-none" />

      {/* Brand Header */}
      <div className="mb-8 z-10 flex flex-col items-center">
        <div className="w-12 h-12 bg-slate-900 border border-slate-800 rounded-xl flex items-center justify-center mb-4 shadow-lg">
          <Shield className="w-6 h-6 text-blue-500" />
        </div>
        <h1 className="text-3xl font-bold tracking-widest text-slate-100">
          GBI<span className="text-blue-600">-SCIOS</span>
        </h1>
        <p className="text-xs text-slate-500 mt-2 uppercase tracking-[0.2em] font-medium">
          Executive Security Module
        </p>
      </div>

      {/* Login Form Component */}
      <div className="z-10 w-full flex justify-center px-4">
        <LoginForm />
      </div>

      {/* Footer */}
      <div className="absolute bottom-8 text-center z-10">
        <p className="text-xs text-slate-600">
          &copy; {new Date().getFullYear()} GBI-SCIOS Sovereign Infrastructure. All rights reserved.
        </p>
        <p className="text-[10px] text-slate-700 mt-1 uppercase tracking-wider">
          Unauthorized access is strictly prohibited
        </p>
      </div>
    </div>
  );
}