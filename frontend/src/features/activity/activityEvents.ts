import { z } from "zod";

const userSummarySchema = z.object({
  id: z.number(),
  email: z.string(),
  full_name: z.string(),
});

const projectSummarySchema = z.object({
  id: z.number(),
  name: z.string(),
  code: z.string(),
  color: z.string(),
  client_id: z.number(),
  client_name: z.string(),
});

export const timeEntrySchema = z.object({
  id: z.number(),
  user: userSummarySchema,
  project: projectSummarySchema,
  description: z.string(),
  started_at: z.string(),
  ended_at: z.string().nullable(),
  duration_seconds: z.number(),
  is_billable: z.boolean(),
  is_running: z.boolean(),
  is_locked: z.boolean(),
  invoice_id: z.number().nullable(),
  created_at: z.string(),
  updated_at: z.string(),
});

const entryPayload = z.object({ entry: timeEntrySchema });

export const activityEventSchema = z.discriminatedUnion("event", [
  z.object({ event: z.literal("timer.started"), payload: entryPayload }),
  z.object({ event: z.literal("timer.stopped"), payload: entryPayload }),
  z.object({ event: z.literal("entry.changed"), payload: entryPayload }),
  z.object({
    event: z.literal("entry.deleted"),
    payload: z.object({ entry_id: z.number(), user_id: z.number() }),
  }),
  z.object({
    event: z.literal("invoice.changed"),
    payload: z.object({ invoice_id: z.number(), status: z.string() }),
  }),
  z.object({ event: z.literal("pong"), payload: z.object({}) }),
  z.object({ event: z.literal("activity.changed"), payload: z.object({}) }),
]);

export type ActivityEvent = z.infer<typeof activityEventSchema>;

export function parseActivityEvent(raw: string): ActivityEvent | null {
  let data: unknown;
  try {
    data = JSON.parse(raw);
  } catch {
    return null;
  }
  const result = activityEventSchema.safeParse(data);
  return result.success ? result.data : null;
}
