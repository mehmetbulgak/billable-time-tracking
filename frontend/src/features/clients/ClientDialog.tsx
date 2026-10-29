import { zodResolver } from "@hookform/resolvers/zod";
import Alert from "@mui/material/Alert";
import Button from "@mui/material/Button";
import Dialog from "@mui/material/Dialog";
import DialogActions from "@mui/material/DialogActions";
import DialogContent from "@mui/material/DialogContent";
import DialogTitle from "@mui/material/DialogTitle";
import InputAdornment from "@mui/material/InputAdornment";
import MenuItem from "@mui/material/MenuItem";
import Stack from "@mui/material/Stack";
import TextField from "@mui/material/TextField";
import { Controller, useForm } from "react-hook-form";

import { useCurrentUser } from "@/features/auth/useCurrentUser";
import { getErrorMessage } from "@/shared/api/errors";
import type { Client } from "@/shared/api/types";
import { useNotify } from "@/shared/feedback/useNotify";

import {
  CURRENCIES,
  clientFormValues,
  clientSchema,
  toClientInput,
  type ClientFormValues,
} from "./clientSchema";
import { useCreateClientMutation, useUpdateClientMutation } from "./clientsApi";

interface ClientDialogProps {
  client: Client | null;
  onClose: () => void;
  onCreated?: (client: Client) => void;
}

export function ClientDialog({ client, onClose, onCreated }: ClientDialogProps) {
  const user = useCurrentUser();
  const notify = useNotify();
  const [createClient, createState] = useCreateClientMutation();
  const [updateClient, updateState] = useUpdateClientMutation();
  const error = client ? updateState.error : createState.error;
  const {
    control,
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ClientFormValues>({
    resolver: zodResolver(clientSchema),
    defaultValues: clientFormValues(client, user.organization.default_currency),
  });

  const onSubmit = handleSubmit(async (values) => {
    const input = toClientInput(values);
    if (client) {
      const result = await updateClient({ id: client.id, ...input });
      if (!("error" in result)) {
        notify.success("Client updated");
        onClose();
      }
      return;
    }
    const result = await createClient(input);
    if (!("error" in result)) {
      notify.success("Client created");
      onCreated?.(result.data);
      onClose();
    }
  });

  return (
    <Dialog open onClose={onClose} maxWidth="sm" fullWidth>
      <form onSubmit={(event) => void onSubmit(event)} noValidate>
        <DialogTitle>{client ? "Edit client" : "New client"}</DialogTitle>
        <DialogContent>
          <Stack spacing={2.5} sx={{ pt: 1 }}>
            {error ? <Alert severity="error">{getErrorMessage(error)}</Alert> : null}
            <TextField
              label="Client name"
              autoFocus
              error={Boolean(errors.name)}
              helperText={errors.name?.message}
              {...register("name")}
            />
            <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
              <TextField label="Contact person" fullWidth {...register("contact_name")} />
              <TextField
                label="Billing email"
                type="email"
                fullWidth
                error={Boolean(errors.email)}
                helperText={errors.email?.message ?? "Invoices are emailed here when issued."}
                {...register("email")}
              />
            </Stack>
            <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
              <Controller
                control={control}
                name="currency"
                render={({ field }) => (
                  <TextField select label="Currency" fullWidth {...field}>
                    {CURRENCIES.map((currency) => (
                      <MenuItem key={currency} value={currency}>
                        {currency}
                      </MenuItem>
                    ))}
                  </TextField>
                )}
              />
              <TextField
                label="Tax rate"
                inputMode="decimal"
                fullWidth
                error={Boolean(errors.tax_rate)}
                helperText={errors.tax_rate?.message}
                slotProps={{
                  input: { endAdornment: <InputAdornment position="end">%</InputAdornment> },
                }}
                {...register("tax_rate")}
              />
              <TextField
                label="Payment terms"
                inputMode="numeric"
                fullWidth
                placeholder={user.organization.default_payment_terms_days.toString()}
                error={Boolean(errors.payment_terms_days)}
                helperText={errors.payment_terms_days?.message}
                slotProps={{
                  input: { endAdornment: <InputAdornment position="end">days</InputAdornment> },
                }}
                {...register("payment_terms_days")}
              />
            </Stack>
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancel</Button>
          <Button
            type="submit"
            variant="contained"
            loading={createState.isLoading || updateState.isLoading}
          >
            {client ? "Save changes" : "Create client"}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}
