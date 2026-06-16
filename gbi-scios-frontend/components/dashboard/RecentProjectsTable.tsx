export default function RecentProjectsTable() {
  const projects = [
    { id: "PRJ-092", name: "GBI-SCIOS Alpha", status: "Critical", exposure: "1.59M SAR", score: "5.07%" },
    { id: "PRJ-093", name: "Riyadh Metro Extension", status: "Review", exposure: "450K SAR", score: "62.40%" },
    { id: "PRJ-094", name: "Jeddah Port Upgrade", status: "Compliant", exposure: "0 SAR", score: "100%" },
  ];

  return (
    <div className="bg-slate-900/50 border border-slate-800 rounded-lg overflow-hidden">
      <div className="p-5 border-b border-slate-800">
        <h3 className="text-sm font-semibold text-slate-200 uppercase tracking-wider">Active Workspace Projects</h3>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-950 text-slate-400">
            <tr>
              <th className="px-5 py-3 font-medium">Project ID</th>
              <th className="px-5 py-3 font-medium">Project Name</th>
              <th className="px-5 py-3 font-medium">Financial Exposure</th>
              <th className="px-5 py-3 font-medium">Compliance Score</th>
              <th className="px-5 py-3 font-medium">Status</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800/50">
            {projects.map((project) => (
              <tr key={project.id} className="hover:bg-slate-800/20 transition-colors">
                <td className="px-5 py-4 text-slate-400 font-mono text-xs">{project.id}</td>
                <td className="px-5 py-4 font-medium text-slate-200">{project.name}</td>
                <td className="px-5 py-4 text-slate-300">{project.exposure}</td>
                <td className="px-5 py-4 text-slate-300">{project.score}</td>
                <td className="px-5 py-4">
                  <span className={`px-2 py-1 rounded-full text-xs font-medium border ${
                    project.status === 'Critical' ? 'bg-red-900/30 text-red-400 border-red-900/50' :
                    project.status === 'Review' ? 'bg-orange-900/30 text-orange-400 border-orange-900/50' :
                    'bg-emerald-900/30 text-emerald-400 border-emerald-900/50'
                  }`}>
                    {project.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}