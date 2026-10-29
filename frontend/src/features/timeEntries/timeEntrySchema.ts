import dayjs, { type Dayjs } from "dayjs";
import { z } from "zod";

const dayjsValue = z.custom<Dayjs>((value) => dayjs.isDayjs(value) && value.isValid(), {
  message: "Enter a valid date and time.",
});

export const timeEntrySchema = z
  .object({
    project: z.number({ error: "Choose a project." }).nullable(),
    description: z.string().max(500, "Keep the description under 500 characters."),
    started_at: dayjsValue,
    ended_at: dayjsValue,
    is_billable: z.boolean(),
  })
  .refine((values) => values.project !== null, {
    path: ["project"],
    message: "Choose a project.",
  })
  .refine((values) => values.ended_at.isAfter(values.started_at), {
    path: ["ended_at"],
    message: "The end time must be after the start time.",
  })
  .refine((values) => !values.ended_at.isAfter(dayjs()), {
    path: ["ended_at"],
    message: "Time entries cannot end in the future.",
  });

export type TimeEntryFormValues = z.infer<typeof timeEntrySchema>;
