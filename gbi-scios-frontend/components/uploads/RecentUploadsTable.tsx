// src/components/uploads/RecentUploadsTable.tsx

import { MoreHorizontal, FileSpreadsheet, FileText, File } from "lucide-react";

const mockUploads = [
  { id: "FL-101", name: "BOQ_Phase1_Final.xlsx", project: "PRJ-092", type: "XLSX", size: "2.4 MB", status: "Processed", date: "2 Hours ago" },
  { id: "FL-102", name: "Mandatory_Materials.csv", project: "PRJ-092", type: "CSV", size: "845 KB", status: "Validating", date: "3 Hours ago" },
  { id: "FL-103", name: "Compliance_Waiver.pdf", project: "PRJ-093", type: "PDF", size: "1.2 MB", status: "Failed", date: "1 Day ago" },
];

const getFileIcon = (type: string) => {
  if (type === "XLSX") return <FileSpreadsheet className="w-4 h-4 text-emerald-500" />;
  if (type === "CSV") return <FileText className="w-4 h-4 text-blue-500" />;
  return <File className="w-4 h-4 text-red-400" />;
};

export default function RecentUploadsTable() {
  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-xl overflow-hidden shadow-xl">
      <div className="p-5 border-b border-slate-800 flex justify-between items-center">
        <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">File Validation & History</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm whitespace-nowrap">
          <thead className="bg-slate-950/80 text-slate-400 border-b border-slate-800">
            <tr>
              <th className="px-6 py-4 font-medium uppercase tracking-wider text-xs">File Name</th>
              <th className="px-6 py-4 font-medium uppercase tracking-wider text-xs">Project</th>
              <th className="px-6 py-4 font-medium uppercase tracking-wider text-xs">Type</th>
              <th className="px-6 py-4 font-medium uppercase tracking-wider text-xs">Size</th>
              <th className="px-6 py-4 font-medium uppercase tracking-wider text-xs">AI Status</th>
              <th className="px-6 py-4 font-medium uppercase tracking-wider text-xs">Uploaded</th>
              <th className="px-6 py-4 font-medium text-right uppercase tracking-wider text-xs">Actions</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/50">
            {mockUploads.map((file) => (
              <tr key={file.id} className="hover:bg-slate-800/30 transition-colors group">
                <td className="px-6 py-4 flex items-center gap-3">
                  <div className="p-2 bg-slate-950 rounded-lg border border-slate-800">
                    {getFileIcon(file.type)}
                  </div>
                  <div>
                    <div className="font-medium text-slate-200">{file.name}</div>
                    <div className="text-xs text-slate-500 mt-0.5 font-mono">{file.id}</div>
                  </div>
                </td>
                <td className="px-6 py-4 text-slate-300 font-mono text-xs">{file.project}</td>
                <td className="px-6 py-4">
                  <span className="px-2 py-1 bg-slate-800 text-slate-300 text-xs rounded font-medium border border-slate-700">
                    {file.type}
                  </span>
                </td>
                <td className="px-6 py-4 text-slate-400">{file.size}</td>
                <td className="px-6 py-4">
                  <span className={`px-2.5 py-1 rounded-md text-xs font-medium border ${
                    file.status === 'Processed' ? 'bg-emerald-950/50 text-emerald-400 border-emerald-900/50' :
                    file.status === 'Failed' ? 'bg-red-950/50 text-red-400 border-red-900/50' :
                    'bg-blue-950/50 text-blue-400 border-blue-900/50 animate-pulse'
                  }`}>
                    {file.status}
                  </span>
                </td>
                <td className="px-6 py-4 text-slate-400 text-xs">{file.date}</td>
                <td className="px-6 py-4 text-right">
                  <button className="text-slate-500 hover:text-slate-300 p-1.5 rounded-md hover:bg-slate-800 transition-colors opacity-0 group-hover:opacity-100">
                    <MoreHorizontal className="w-5 h-5" />
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}