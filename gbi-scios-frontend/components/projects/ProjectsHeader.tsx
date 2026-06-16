"use client";

import { Search, Plus, Filter } from "lucide-react";

interface ProjectsHeaderProps {
  onSearch: (term: string) => void;
  onCreateClick: () => void;
}

export default function ProjectsHeader({ onSearch, onCreateClick }: ProjectsHeaderProps) {
  return (
    <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4 mb-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-100 tracking-tight">Projects Workspace</h1>
        <p className="text-sm text-slate-400 mt-1">Manage and monitor enterprise compliance across all active deployments.</p>
      </div>
      <div className="flex items-center gap-3 w-full md:w-auto">
        <div className="relative flex-1 md:w-64">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-4 w-4 text-slate-500" />
          </div>
          <input
            type="text"
            onChange={(e) => onSearch(e.target.value)}
            placeholder="Filter systems cache..."
            className="block w-full pl-9 pr-3 py-2 bg-slate-900 border border-slate-800 rounded-lg text-sm text-slate-200 placeholder-slate-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-colors"
          />
        </div>
        
        <button className="p-2 bg-slate-900 border border-slate-800 rounded-lg text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors">
          <Filter className="w-4 h-4" />
        </button>
        
        <button 
          onClick={onCreateClick}
          className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 text-white text-sm font-medium py-2 px-4 rounded-lg transition-colors shadow-lg shadow-blue-900/20"
        >
          <Plus className="w-4 h-4" />
          Initialize Node
        </button>
      </div>
    </div>
  );
}