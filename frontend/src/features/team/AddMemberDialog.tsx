import { zodResolver } from "@hookform/resolvers/zod";
import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import MenuItem from "@mui/material/MenuItem";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import { Controller, useForm } from "react-hook-form";
import { z } from "zod";

import { useCurrentUser } from "@/features/auth/useCurrentUser";
import { getErrorMessage } from "@/shared/api/errors";
import { useNotify } from "@/shared/feedback/useNotify";

import { useCreateMemberMutation } from "./membersApi";
import { assignableRoles, ROLE_LABELS } from "./roles";

const memberSchema = z.object({
  first_name: z.string().trim().min(1, "Enter a first name.").max(80),
  last_name: z.string().trim().min(1, "Enter a last name.").max(80),
  email: z.email("Enter a valid email address."),
  role: z.enum(["owner", "manager", "member"]),
  password: z.string().min(10, "Use at least 10 characters."),
});

type MemberFormValues = z.infer<typeof memberSchema>;

export function AddMemberDialog({ onClose }: { onClose: () => void }) {
  const user = useCurrentUser();
  const notify = useNotify();
  const [createMember, { isLoading, error }] = useCreateMemberMutation();
  const {
    control,
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<MemberFormValues>({
    resolver: zodResolver(memberSchema),
    defaultValues: { first_name: "", last_name: "", email: "", role: "member", password: "" },
  });

  const onSubmit = handleSubmit(async (values) => {
    const result = await createMember(values);
    if (!("error" in result)) {
      notify.success(`${result.data.full_name} joined the team`);
      onClose();
    }
  });

  return (
    <Dialog open onClose={onClose} maxWidth="sm" fullWidth>
      <form onSubmit={(event) => void onSubmit(event)} noValidate>
        <DialogTitle>Add team member</DialogTitle>
        <DialogContent>
          <Stack spacing={2.5} sx={{ pt: 1 }}>
            {error ? <Alert severity="error">{getErrorMessage(error)}</Alert> : null}
            <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
              <TextField
                label="First name"
                autoFocus
                fullWidth
                error={Boolean(errors.first_name)}
                helperText={errors.first_name?.message}
                {...register("first_name")}
              />
              <TextField
                label="Last name"
                fullWidth
                error={Boolean(errors.last_name)}
                helperText={errors.last_name?.message}
                {...register("last_name")}
              />
            </Stack>
            <TextField
              label="Email"
              type="email"
              error={Boolean(errors.email)}
              helperText={errors.email?.message}
              {...register("email")}
            />
            <Controller
              control={control}
              name="role"
              render={({ field }) => (
                <TextField select label="Role" {...field}>
                  {assignableRoles(user).map((role) => (
                    <MenuItem key={role} value={role}>
                      {ROLE_LABELS[role]}
                    </MenuItem>
                  ))}
                </TextField>
              )}
            />
            <TextField
              label="Temporary password"
              type="password"
              autoComplete="new-password"
              error={Boolean(errors.password)}
              helperText={errors.password?.message ?? "Share it with the new member securely."}
              {...register("password")}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancel</Button>
          <Button type="submit" variant="contained" loading={isLoading}>
            Add member
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}
