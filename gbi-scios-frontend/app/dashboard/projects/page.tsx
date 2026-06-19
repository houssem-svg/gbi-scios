"use client";

import { Suspense, useCallback, useEffect, useState } from "react";
import dynamic from "next/dynamic";
import ProjectsHeader from "@/components/projects/ProjectsHeader";
import ProjectsTable from "@/components/projects/ProjectsTable";
import { projectService } from "@/lib/projectService";
import { Project, ProjectCreateInput, ProjectUpdateInput } from "@/types/project";

/**
 * Audit item C-2/C-5/C-11: lazy-load the modals via next/dynamic so their
 * react-hook-form + heavy form logic ship only when the user opens them.
 * Wrapped in <Suspense> with a minimal fallback per spec.
 */
const ProjectModal = dynamic(
  () => import("@/components/projects/ProjectModal"),
  { ssr: false },
);
const DeleteConfirmModal = dynamic(
  () => import("@/components/projects/DeleteConfirmModal"),
  { ssr: false },
);

export default function ProjectsWorkspacePage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [filteredProjects, setFilteredProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal State Management
  const [isProjectModalOpen, setIsProjectModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);

  // FE-15: wrap fetch in useCallback so it can be a stable dep of useEffect.
  const fetchWorkspace = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await projectService.getAllProjects({ skip: 0, limit: 100 });
      setProjects(data);
      setFilteredProjects(data);
    } catch (err) {
      const msg = err instanceof Error ? err.message : "Failed to load projects.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchWorkspace();
  }, [fetchWorkspace]);

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

      <Suspense fallback={<div>Loading…</div>}>
        <ProjectModal
          isOpen={isProjectModalOpen}
          onClose={() => setIsProjectModalOpen(false)}
          onSubmit={handleFormSubmit}
          project={selectedProject}
        />
      </Suspense>

      <Suspense fallback={<div>Loading…</div>}>
        <DeleteConfirmModal
          isOpen={isDeleteModalOpen}
          onClose={() => setIsDeleteModalOpen(false)}
          onConfirm={handleDeleteExecute}
          projectName={selectedProject?.name || ""}
        />
      </Suspense>
    </div>
  );
}
