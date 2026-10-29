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
import ToggleButton from "@mui/material/ToggleButton";
import ToggleButtonGroup from "@mui/material/ToggleButtonGroup";
import Typography from "@mui/material/Typography";
import { DatePicker } from "@mui/x-date-pickers/DatePicker";
import { Controller, useForm, useWatch } from "react-hook-form";

import { getErrorMessage } from "@/shared/api/errors";
import type { BillingModel, Client } from "@/shared/api/types";
import { useNotify } from "@/shared/feedback/useNotify";

import {
  contractSchema,
  emptyContractForm,
  requiredFieldsFor,
  toContractInput,
  type ContractFormValues,
} from "./contractSchema";
import { useCreateContractMutation } from "./contractsApi";
import { BILLING_MODEL_LABELS, ROUNDING_OPTIONS } from "./contractTerms";

const MODEL_HELP: Record<BillingModel, string> = {
  hourly: "Every billable hour is invoiced at the hourly rate.",
  retainer:
    "A monthly fee covers the included hours. Extra hours are billed as overage and unused hours can roll into the next month.",
  fixed_fee: "A fixed monthly fee. Hours are tracked for profitability only.",
};

interface ContractDialogProps {
  client: Client;
  onClose: () => void;
}

export function ContractDialog({ client, onClose }: ContractDialogProps) {
  const notify = useNotify();
  const [createContract, { isLoading, error }] = useCreateContractMutation();
  const {
    control,
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ContractFormValues>({
    resolver: zodResolver(contractSchema),
    defaultValues: emptyContractForm(),
  });
  const billingModel = useWatch({ control, name: "billing_model" });
  const visibleFields = requiredFieldsFor(billingModel);

  const onSubmit = handleSubmit(async (values) => {
    const result = await createContract(toContractInput(client.id, values));
    if (!("error" in result)) {
      notify.success("Contract created");
      onClose();
    }
  });

  const moneyAdornment = {
    input: { startAdornment: <InputAdornment position="start">{client.currency}</InputAdornment> },
  };
  const hoursAdornment = {
    input: { endAdornment: <InputAdornment position="end">h</InputAdornment> },
  };

  return (
    <Dialog open onClose={onClose} maxWidth="sm" fullWidth>
      <form onSubmit={(event) => void onSubmit(event)} noValidate>
        <DialogTitle>New contract for {client.name}</DialogTitle>
        <DialogContent>
          <Stack spacing={2.5} sx={{ pt: 1 }}>
            {error ? <Alert severity="error">{getErrorMessage(error)}</Alert> : null}
            <Controller
              control={control}
              name="billing_model"
              render={({ field }) => (
                <ToggleButtonGroup
                  exclusive
                  fullWidth
                  color="primary"
                  value={field.value}
                  onChange={(_event, value: BillingModel | null) => {
                    if (value) {
                      field.onChange(value);
                    }
                  }}
                >
                  {(Object.keys(BILLING_MODEL_LABELS) as BillingModel[]).map((model) => (
                    <ToggleButton key={model} value={model}>
                      {BILLING_MODEL_LABELS[model]}
                    </ToggleButton>
                  ))}
                </ToggleButtonGroup>
              )}
            />
            <Typography variant="body2" color="text.secondary">
              {MODEL_HELP[billingModel]}
            </Typography>
            <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
              <Controller
                control={control}
                name="starts_on"
                render={({ field }) => (
                  <DatePicker
                    label="Starts on"
                    value={field.value}
                    onChange={(value) => {
                      field.onChange(value);
                    }}
                    slotProps={{
                      textField: {
                        fullWidth: true,
                        error: Boolean(errors.starts_on),
                        helperText: errors.starts_on?.message,
                      },
                    }}
                  />
                )}
              />
              <Controller
                control={control}
                name="ends_on"
                render={({ field }) => (
                  <DatePicker
                    label="Ends on (optional)"
                    value={field.value}
                    onChange={(value) => {
                      field.onChange(value);
                    }}
                    slotProps={{
                      field: { clearable: true },
                      textField: {
                        fullWidth: true,
                        error: Boolean(errors.ends_on),
                        helperText: errors.ends_on?.message,
                      },
                    }}
                  />
                )}
              />
            </Stack>
            {visibleFields.includes("hourly_rate") ? (
              <TextField
                label="Hourly rate"
                inputMode="decimal"
                error={Boolean(errors.hourly_rate)}
                helperText={errors.hourly_rate?.message}
                slotProps={moneyAdornment}
                {...register("hourly_rate")}
              />
            ) : null}
            {visibleFields.includes("monthly_fee") ? (
              <TextField
                label="Monthly fee"
                inputMode="decimal"
                error={Boolean(errors.monthly_fee)}
                helperText={errors.monthly_fee?.message}
                slotProps={moneyAdornment}
                {...register("monthly_fee")}
              />
            ) : null}
            {billingModel === "retainer" ? (
              <>
                <Stack direction={{ xs: "column", sm: "row" }} spacing={2}>
                  <TextField
                    label="Included hours"
                    inputMode="decimal"
                    fullWidth
                    error={Boolean(errors.included_hours)}
                    helperText={errors.included_hours?.message}
                    slotProps={hoursAdornment}
                    {...register("included_hours")}
                  />
                  <TextField
                    label="Overage rate"
                    inputMode="decimal"
                    fullWidth
                    error={Boolean(errors.overage_rate)}
                    helperText={errors.overage_rate?.message}
                    slotProps={moneyAdornment}
                    {...register("overage_rate")}
                  />
                </Stack>
                <TextField
                  label="Rollover cap"
                  inputMode="decimal"
                  error={Boolean(errors.rollover_cap_hours)}
                  helperText={
                    errors.rollover_cap_hours?.message ??
                    "Unused included hours that may carry into the next month."
                  }
                  slotProps={hoursAdornment}
                  {...register("rollover_cap_hours")}
                />
              </>
            ) : null}
            <Controller
              control={control}
              name="rounding_increment_minutes"
              render={({ field }) => (
                <TextField
                  select
                  label="Round each entry up to"
                  value={field.value}
                  onChange={(event) => {
                    field.onChange(Number(event.target.value));
                  }}
                >
                  {ROUNDING_OPTIONS.map((option) => (
                    <MenuItem key={option.value} value={option.value}>
                      {option.label}
                    </MenuItem>
                  ))}
                </TextField>
              )}
            />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={onClose}>Cancel</Button>
          <Button type="submit" variant="contained" loading={isLoading}>
            Create contract
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
}
