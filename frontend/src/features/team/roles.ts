import type { CurrentUser, Member, Role } from "@/shared/api/types";

export const ROLE_LABELS: Record<Role, string> = {
  owner: "Owner",
  manager: "Manager",
  member: "Member",
};

export const assignableRoles = (actor: Pick<CurrentUser, "role">): Role[] =>
  actor.role === "owner" ? ["owner", "manager", "member"] : ["manager", "member"];

export const canManageMember = (
  actor: Pick<CurrentUser, "id" | "role" | "is_manager">,
  member: Member,
): boolean =>
  actor.is_manager && actor.id !== member.id && (member.role !== "owner" || actor.role === "owner");
