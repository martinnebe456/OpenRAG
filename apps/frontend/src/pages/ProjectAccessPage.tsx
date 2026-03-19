import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiClient } from "../api/client";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { FormDialog } from "../components/FormDialog";
import { PageCard } from "../components/Ui";
import { useUiStore } from "../store/uiStore";

type ProjectRow = {
  id: string;
  name: string;
  slug: string;
  description?: string | null;
  is_active: boolean;
  my_role?: string | null;
};

type ProjectMember = {
  project_id: string;
  user_id: string;
  username: string;
  email: string;
  display_name: string;
  role: "viewer" | "contributor" | "manager";
  membership_active: boolean;
  is_active: boolean;
};

type AssignableUser = {
  id: string;
  username: string;
  email: string;
  display_name: string;
  is_active: boolean;
};

export function ProjectAccessPage() {
  const qc = useQueryClient();
  const addToast = useUiStore((s) => s.addToast);
  const [selectedProjectId, setSelectedProjectId] = useState<string | null>(null);
  const [isEditProjectOpen, setIsEditProjectOpen] = useState(false);
  const [editProjectName, setEditProjectName] = useState("");
  const [editProjectDescription, setEditProjectDescription] = useState("");
  const [isAddMemberOpen, setIsAddMemberOpen] = useState(false);
  const [memberUserId, setMemberUserId] = useState("");
  const [memberRole, setMemberRole] = useState<"viewer" | "contributor" | "manager">("viewer");
  const [assignableSearch, setAssignableSearch] = useState("");
  const [memberToRemove, setMemberToRemove] = useState<ProjectMember | null>(null);

  const projectsQuery = useQuery({
    queryKey: ["projects"],
    queryFn: async () => apiClient.get<{ items: ProjectRow[] }>("/projects"),
  });

  const manageableProjects = useMemo(
    () => (projectsQuery.data?.items ?? []).filter((project) => project.my_role === "manager"),
    [projectsQuery.data],
  );

  useEffect(() => {
    if (!manageableProjects.length) {
      setSelectedProjectId(null);
      return;
    }
    if (!selectedProjectId || !manageableProjects.some((project) => project.id === selectedProjectId)) {
      setSelectedProjectId(manageableProjects[0].id);
    }
  }, [manageableProjects, selectedProjectId]);

  const selectedProject = useMemo(
    () => manageableProjects.find((project) => project.id === selectedProjectId) ?? null,
    [manageableProjects, selectedProjectId],
  );

  const membersQuery = useQuery({
    queryKey: ["project-members", selectedProjectId],
    queryFn: async () => {
      if (!selectedProjectId) return { items: [] as ProjectMember[] };
      return apiClient.get<{ items: ProjectMember[] }>(`/projects/${selectedProjectId}/members`);
    },
    enabled: !!selectedProjectId,
  });

  const assignableUsersQuery = useQuery({
    queryKey: ["project-assignable-users", selectedProjectId, assignableSearch],
    queryFn: async () => {
      if (!selectedProjectId) return { items: [] as AssignableUser[] };
      const search = assignableSearch.trim();
      const suffix = search ? `?search=${encodeURIComponent(search)}` : "";
      return apiClient.get<{ items: AssignableUser[] }>(`/projects/${selectedProjectId}/assignable-users${suffix}`);
    },
    enabled: isAddMemberOpen && !!selectedProjectId,
  });

  const updateProjectMutation = useMutation({
    mutationFn: async (body: Record<string, unknown>) => {
      if (!selectedProjectId) throw new Error("No project selected");
      return apiClient.patch<ProjectRow>(`/projects/${selectedProjectId}`, body);
    },
    onSuccess: async () => {
      addToast({ title: "Project updated", kind: "success" });
      setIsEditProjectOpen(false);
      await qc.invalidateQueries({ queryKey: ["projects"] });
    },
    onError: (error) => addToast({ title: "Project update failed", message: (error as Error).message, kind: "error" }),
  });

  const addMemberMutation = useMutation({
    mutationFn: async () => {
      if (!selectedProjectId) throw new Error("No project selected");
      if (!memberUserId) throw new Error("Select a user");
      return apiClient.post(`/projects/${selectedProjectId}/members`, {
        user_id: memberUserId,
        role: memberRole,
        is_active: true,
      });
    },
    onSuccess: async () => {
      addToast({ title: "Member added", kind: "success" });
      setMemberUserId("");
      setMemberRole("viewer");
      setAssignableSearch("");
      setIsAddMemberOpen(false);
      await qc.invalidateQueries({ queryKey: ["project-members", selectedProjectId] });
      await qc.invalidateQueries({ queryKey: ["project-assignable-users", selectedProjectId] });
    },
    onError: (error) => addToast({ title: "Add member failed", message: (error as Error).message, kind: "error" }),
  });

  const updateMemberMutation = useMutation({
    mutationFn: async ({ userId, body }: { userId: string; body: Record<string, unknown> }) => {
      if (!selectedProjectId) throw new Error("No project selected");
      return apiClient.patch(`/projects/${selectedProjectId}/members/${userId}`, body);
    },
    onSuccess: async () => {
      addToast({ title: "Membership updated", kind: "success" });
      await qc.invalidateQueries({ queryKey: ["project-members", selectedProjectId] });
      await qc.invalidateQueries({ queryKey: ["projects"] });
    },
    onError: (error) => addToast({ title: "Membership update failed", message: (error as Error).message, kind: "error" }),
  });

  const deleteMemberMutation = useMutation({
    mutationFn: async (userId: string) => {
      if (!selectedProjectId) throw new Error("No project selected");
      return apiClient.delete(`/projects/${selectedProjectId}/members/${userId}`);
    },
    onSuccess: async () => {
      addToast({ title: "Member removed", kind: "success" });
      setMemberToRemove(null);
      await qc.invalidateQueries({ queryKey: ["project-members", selectedProjectId] });
      await qc.invalidateQueries({ queryKey: ["project-assignable-users", selectedProjectId] });
    },
    onError: (error) => addToast({ title: "Remove member failed", message: (error as Error).message, kind: "error" }),
  });

  return (
    <div className="grid gap-4 xl:grid-cols-[0.95fr_1.05fr]">
      <PageCard title="Managed Projects" subtitle="Projects where you are responsible for membership and access.">
        <div className="space-y-2">
          {manageableProjects.map((project) => (
            <button
              key={project.id}
              type="button"
              onClick={() => setSelectedProjectId(project.id)}
              className={`surface-soft w-full rounded-xl border p-3 text-left transition ${
                selectedProjectId === project.id
                  ? "border-ink/15 bg-ink text-paper"
                  : "border-ink/10 text-ink hover:bg-white/75"
              }`}
            >
              <div className="font-medium">{project.name}</div>
              <div className={`text-xs ${selectedProjectId === project.id ? "text-paper/80" : "text-ink/55"}`}>
                {project.slug} · {project.is_active ? "active" : "inactive"}
              </div>
            </button>
          ))}
          {!projectsQuery.isLoading && manageableProjects.length === 0 && (
            <div className="rounded-xl border border-dashed border-ink/10 p-5 text-sm text-ink/60">
              You do not manage any project yet. An admin must first create the project and assign you as its owner.
            </div>
          )}
        </div>
      </PageCard>

      <div className="grid gap-4">
        <PageCard
          title="Project Details"
          subtitle={selectedProject ? "Owner-level metadata for this project" : "Select a managed project"}
          actions={
            selectedProject ? (
              <button
                type="button"
                onClick={() => {
                  setEditProjectName(selectedProject.name);
                  setEditProjectDescription(selectedProject.description ?? "");
                  setIsEditProjectOpen(true);
                }}
                className="rounded-lg border border-ink/12 bg-white/85 px-3 py-2 text-sm"
              >
                Edit
              </button>
            ) : undefined
          }
        >
          {!selectedProject ? (
            <div className="text-sm text-ink/60">Select a project from the list.</div>
          ) : (
            <div className="rounded-xl border border-ink/10 bg-white/70 p-4 text-sm text-ink/70">
              <div>
                <span className="font-semibold text-ink">Name:</span> {selectedProject.name}
              </div>
              <div>
                <span className="font-semibold text-ink">Slug:</span> {selectedProject.slug}
              </div>
              <div>
                <span className="font-semibold text-ink">Status:</span> {selectedProject.is_active ? "active" : "inactive"}
              </div>
              {selectedProject.description && (
                <div className="mt-2">
                  <span className="font-semibold text-ink">Description:</span> {selectedProject.description}
                </div>
              )}
            </div>
          )}
        </PageCard>

        <PageCard
          title="Project Members"
          subtitle={selectedProject ? `Existing users with access to ${selectedProject.name}` : "Select a project to manage members"}
          actions={
            selectedProjectId ? (
              <button
                type="button"
                onClick={() => setIsAddMemberOpen(true)}
                className="rounded-lg bg-ink px-3 py-2 text-sm font-medium text-paper"
              >
                Add Member
              </button>
            ) : undefined
          }
        >
          {!selectedProjectId ? (
            <div className="text-sm text-ink/60">Select a project first.</div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-ink/10 text-xs uppercase tracking-[0.12em] text-ink/60">
                    <th className="px-2 py-2">User</th>
                    <th className="px-2 py-2">Role</th>
                    <th className="px-2 py-2">Membership</th>
                    <th className="px-2 py-2">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {(membersQuery.data?.items ?? []).map((member) => (
                    <tr key={member.user_id} className="border-b border-ink/5 hover:bg-white/35">
                      <td className="px-2 py-2">
                        <div className="font-medium text-ink">{member.display_name}</div>
                        <div className="text-xs text-ink/55">{member.username}</div>
                        <div className="text-xs text-ink/55">{member.email}</div>
                      </td>
                      <td className="px-2 py-2">
                        <select
                          value={member.role}
                          onChange={(e) => updateMemberMutation.mutate({ userId: member.user_id, body: { role: e.target.value } })}
                          className="rounded-md border border-ink/12 bg-white/85 px-2 py-1 text-xs"
                        >
                          <option value="viewer">viewer</option>
                          <option value="contributor">contributor</option>
                          <option value="manager">manager</option>
                        </select>
                      </td>
                      <td className="px-2 py-2">
                        <span
                          className={`rounded-full border px-2 py-1 text-xs ${
                            member.membership_active
                              ? "border-[#3674B5]/35 bg-[#578FCA]/12 text-[#3674B5]"
                              : "border-[#578FCA]/25 bg-white/80 text-[#3674B5]/80"
                          }`}
                        >
                          {member.membership_active ? "active" : "inactive"}
                        </span>
                      </td>
                      <td className="px-2 py-2">
                        <div className="flex flex-wrap gap-2">
                          <button
                            type="button"
                            onClick={() => updateMemberMutation.mutate({ userId: member.user_id, body: { is_active: !member.membership_active } })}
                            className="rounded-md border border-ink/12 bg-white/85 px-2 py-1 text-xs"
                          >
                            {member.membership_active ? "Disable" : "Enable"}
                          </button>
                          <button
                            type="button"
                            onClick={() => setMemberToRemove(member)}
                            className="rounded-md border border-[#FADA7A]/80 bg-[#F5F0CD]/95 px-2 py-1 text-xs text-ink"
                          >
                            Remove
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
              {(membersQuery.data?.items.length ?? 0) === 0 && (
                <div className="mt-3 rounded-xl border border-dashed border-ink/10 p-5 text-sm text-ink/60">
                  No members assigned to this project yet.
                </div>
              )}
            </div>
          )}
        </PageCard>
      </div>

      <FormDialog
        open={isEditProjectOpen}
        onOpenChange={setIsEditProjectOpen}
        title="Edit project"
        description={selectedProject ? `Update metadata for ${selectedProject.name}.` : undefined}
        submitLabel="Save changes"
        isSubmitting={updateProjectMutation.isPending}
        onSubmit={() => {
          if (!editProjectName.trim()) {
            addToast({ title: "Name required", kind: "warning" });
            return;
          }
          updateProjectMutation.mutate({
            name: editProjectName.trim(),
            description: editProjectDescription.trim() || null,
          });
        }}
      >
        <input
          value={editProjectName}
          onChange={(e) => setEditProjectName(e.target.value)}
          placeholder="Project name"
          className="w-full rounded-lg border border-ink/12 bg-white px-3 py-2 text-sm"
        />
        <textarea
          value={editProjectDescription}
          onChange={(e) => setEditProjectDescription(e.target.value)}
          placeholder="Description (optional)"
          className="h-24 w-full rounded-lg border border-ink/12 bg-white px-3 py-2 text-sm"
        />
      </FormDialog>

      <FormDialog
        open={isAddMemberOpen}
        onOpenChange={(open) => {
          setIsAddMemberOpen(open);
          if (!open && !addMemberMutation.isPending) {
            setMemberUserId("");
            setMemberRole("viewer");
            setAssignableSearch("");
          }
        }}
        title="Add project member"
        description={selectedProject ? `Grant access to ${selectedProject.name}. Only existing active system users are eligible.` : undefined}
        submitLabel="Add member"
        isSubmitting={addMemberMutation.isPending}
        onSubmit={() => {
          if (!memberUserId) {
            addToast({ title: "Select user", kind: "warning" });
            return;
          }
          addMemberMutation.mutate();
        }}
      >
        <input
          value={assignableSearch}
          onChange={(e) => setAssignableSearch(e.target.value)}
          placeholder="Search existing users..."
          className="w-full rounded-lg border border-ink/12 bg-white px-3 py-2 text-sm"
        />
        <select
          value={memberUserId}
          onChange={(e) => setMemberUserId(e.target.value)}
          className="w-full rounded-lg border border-ink/12 bg-white px-3 py-2 text-sm"
        >
          <option value="">Select user</option>
          {(assignableUsersQuery.data?.items ?? []).map((user) => (
            <option key={user.id} value={user.id}>
              {user.display_name} ({user.username})
            </option>
          ))}
        </select>
        <select
          value={memberRole}
          onChange={(e) => setMemberRole(e.target.value as "viewer" | "contributor" | "manager")}
          className="w-full rounded-lg border border-ink/12 bg-white px-3 py-2 text-sm"
        >
          <option value="viewer">viewer</option>
          <option value="contributor">contributor</option>
          <option value="manager">manager</option>
        </select>
      </FormDialog>

      <ConfirmDialog
        open={!!memberToRemove}
        onOpenChange={(open) => {
          if (!open) setMemberToRemove(null);
        }}
        title="Remove member"
        description={memberToRemove ? `Remove ${memberToRemove.display_name} from this project?` : undefined}
        confirmLabel="Remove"
        tone="warning"
        isPending={deleteMemberMutation.isPending}
        onConfirm={() => {
          if (!memberToRemove) return;
          deleteMemberMutation.mutate(memberToRemove.user_id);
        }}
      />
    </div>
  );
}
