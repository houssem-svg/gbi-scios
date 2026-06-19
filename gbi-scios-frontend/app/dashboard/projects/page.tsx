"use client";

import { useEffect, useState } from "react";
import ProjectsHeader from "@/components/projects/ProjectsHeader";
import ProjectsTable from "@/components/projects/ProjectsTable";
import ProjectModal from "@/components/projects/ProjectModal";
import DeleteConfirmModal from "@/components/projects/DeleteConfirmModal";
import { projectService } from "@/lib/projectService";
import { Project, ProjectCreateInput, ProjectUpdateInput } from "@/types/project";

export default function ProjectsWorkspacePage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [filteredProjects, setFilteredProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal State Management
  const [isProjectModalOpen, setIsProjectModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);

  const fetchWorkspace = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await projectService.getAllProjects();
      setProjects(data);
      setFilteredProjects(data);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to load projects.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchWorkspace();
  }, []);

  const handleSearch = (term: string) => {
    const searchTerm = term.toLowerCase();
    const output = projects.filter(
      (p) =>
        (p.name || "").toLowerCase().includes(searchTerm) ||
        (p.client || "").toLowerCase().includes(searchTerm) ||
        (p.sector || "").toLowerCase().includes(searchTerm),
    );
    setFilteredProjects(output);
  };

  const handleFormSubmit = async (formData: ProjectCreateInput | ProjectUpdateInput) => {
    try {
      if (selectedProject) {
        await projectService.updateProject(selectedProject.id, formData as ProjectUpdateInput);
      } else {
        await projectService.createProject(formData as ProjectCreateInput);
      }
      await fetchWorkspace();
      setIsProjectModalOpen(false);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Operation rejected by the server.";
      alert(msg);
    }
  };

  const handleDeleteExecute = async () => {
    if (!selectedProject) return;
    try {
      await projectService.deleteProject(selectedProject.id);
      await fetchWorkspace();
      setIsDeleteModalOpen(false);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to delete project.";
      alert(msg);
    }
  };

  return (
    <div className="max-w-7xl mx-auto animate-in fade-in duration-500 space-y-4">
      {error && (
        <div className="p-3 bg-red-950/40 border border-red-900/50 rounded-lg text-xs font-mono text-red-400">
          SYSTEM_ERROR_STATE: {error}
        </div>
      )}

      <ProjectsHeader
        onSearch={handleSearch}
        onCreateClick={() => {
          setSelectedProject(null);
          setIsProjectModalOpen(true);
        }}
      />

      <ProjectsTable
        projects={filteredProjects}
        loading={loading}
        onEditClick={(project) => {
          setSelectedProject(project);
          setIsProjectModalOpen(true);
        }}
        onDeleteClick={(project) => {
          setSelectedProject(project);
          setIsDeleteModalOpen(true);
        }}
      />

      <ProjectModal
        isOpen={isProjectModalOpen}
        onClose={() => setIsProjectModalOpen(false)}
        onSubmit={handleFormSubmit}
        project={selectedProject}
      />

      <DeleteConfirmModal
        isOpen={isDeleteModalOpen}
        onClose={() => setIsDeleteModalOpen(false)}
        onConfirm={handleDeleteExecute}
        projectName={selectedProject?.name || ""}
      />
    </div>
  );
}
