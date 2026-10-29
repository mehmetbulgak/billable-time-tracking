import PersonAddOutlined from "@mui/icons-material/PersonAddOutlined";
import Avatar from "@mui/material/Avatar";
import Button from "@mui/material/Button";
import Card from "@mui/material/Card";
import Chip from "@mui/material/Chip";
import MenuItem from "@mui/material/MenuItem";
import Stack from "@mui/material/Stack";
import Switch from "@mui/material/Switch";
import Table from "@mui/material/Table";
import TableBody from "@mui/material/TableBody";
import TableCell from "@mui/material/TableCell";
import TableContainer from "@mui/material/TableContainer";
import TableHead from "@mui/material/TableHead";
import TableRow from "@mui/material/TableRow";
import TextField from "@mui/material/TextField";
import Tooltip from "@mui/material/Tooltip";
import Typography from "@mui/material/Typography";
import { useState } from "react";

import { useCurrentUser } from "@/features/auth/useCurrentUser";
import type { Member, Role } from "@/shared/api/types";
import { ErrorState } from "@/shared/components/ErrorState";
import { LoadingState } from "@/shared/components/LoadingState";
import { PageHeader } from "@/shared/components/PageHeader";
import { useNotify } from "@/shared/feedback/useNotify";
import { formatDate } from "@/shared/lib/format";

import { AddMemberDialog } from "./AddMemberDialog";
import { useListMembersQuery, useUpdateMemberMutation } from "./membersApi";
import { assignableRoles, canManageMember, ROLE_LABELS } from "./roles";

export function TeamPage() {
  const user = useCurrentUser();
  const notify = useNotify();
  const [adding, setAdding] = useState(false);
  const { data, isLoading, error, refetch } = useListMembersQuery({});
  const [updateMember] = useUpdateMemberMutation();

  const update = async (member: Member, patch: { role?: Role; is_active?: boolean }) => {
    const result = await updateMember({ id: member.id, ...patch });
    if ("error" in result) {
      notify.error(result.error);
    } else {
      notify.success(`${member.full_name} updated`);
    }
  };

  const renderTable = () => {
    if (isLoading) {
      return <LoadingState />;
    }
    if (error || !data) {
      return <ErrorState error={error} onRetry={() => void refetch()} />;
    }
    return (
      <TableContainer>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Member</TableCell>
              <TableCell>Role</TableCell>
              <TableCell>Joined</TableCell>
              <TableCell align="right">Active</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {data.results.map((member) => {
              const manageable = canManageMember(user, member);
              return (
                <TableRow key={member.id} hover sx={{ opacity: member.is_active ? 1 : 0.55 }}>
                  <TableCell>
                    <Stack direction="row" spacing={1.5} sx={{ alignItems: "center" }}>
                      <Avatar
                        sx={{ width: 36, height: 36, fontSize: 14, bgcolor: "primary.light" }}
                      >
                        {member.first_name.charAt(0)}
                        {member.last_name.charAt(0)}
                      </Avatar>
                      <Stack>
                        <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
                          <Typography variant="subtitle2">{member.full_name}</Typography>
                          {member.id === user.id ? <Chip size="small" label="You" /> : null}
                        </Stack>
                        <Typography variant="caption" color="text.secondary">
                          {member.email}
                        </Typography>
                      </Stack>
                    </Stack>
                  </TableCell>
                  <TableCell sx={{ width: 200 }}>
                    {manageable ? (
                      <TextField
                        select
                        size="small"
                        value={member.role}
                        onChange={(event) =>
                          void update(member, { role: event.target.value as Role })
                        }
                        slotProps={{ htmlInput: { "aria-label": `Role of ${member.full_name}` } }}
                        fullWidth
                      >
                        {assignableRoles(user).map((role) => (
                          <MenuItem key={role} value={role}>
                            {ROLE_LABELS[role]}
                          </MenuItem>
                        ))}
                      </TextField>
                    ) : (
                      <Chip
                        size="small"
                        label={ROLE_LABELS[member.role]}
                        color={member.role === "member" ? "default" : "primary"}
                        variant="outlined"
                      />
                    )}
                  </TableCell>
                  <TableCell>{formatDate(member.date_joined)}</TableCell>
                  <TableCell align="right">
                    <Tooltip title={manageable ? "" : "You cannot change this member"}>
                      <span>
                        <Switch
                          checked={member.is_active}
                          disabled={!manageable}
                          onChange={(event) =>
                            void update(member, { is_active: event.target.checked })
                          }
                          slotProps={{ input: { "aria-label": `${member.full_name} is active` } }}
                        />
                      </span>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </TableContainer>
    );
  };

  return (
    <>
      <PageHeader
        title="Team"
        subtitle={`Everyone at ${user.organization.name}`}
        actions={
          user.is_manager ? (
            <Button
              variant="contained"
              startIcon={<PersonAddOutlined />}
              onClick={() => {
                setAdding(true);
              }}
            >
              Add member
            </Button>
          ) : null
        }
      />
      <Card>{renderTable()}</Card>
      {adding ? (
        <AddMemberDialog
          onClose={() => {
            setAdding(false);
          }}
        />
      ) : null}
    </>
  );
}
