import { z } from 'zod';

export const TimeSlotSchema = z.object({
  id: z.string(),
  start: z.string(), // ISO string
  end: z.string(),   // ISO string
  isAvailable: z.boolean(),
});

export const ParticipantSchema = z.object({
  id: z.string(),
  name: z.string(),
  availability: z.array(z.string()), // Array of TimeSlot IDs
});

export const MeetingSchema = z.object({
  id: z.string(),
  title: z.string(),
  priority: z.number().min(1).max(10),
  durationMinutes: z.number(),
  deadline: z.string(), // ISO string
  participants: z.array(z.string()), // Array of Participant IDs
  scheduledSlotId: z.string().optional(),
});

export const ObservationSchema = z.object({
  calendar: z.array(TimeSlotSchema),
  meetings: z.array(MeetingSchema),
  participants: z.array(ParticipantSchema),
  currentStep: z.number(),
  maxSteps: z.number(),
});

export const ActionSchema = z.union([
  z.object({
    type: z.literal('schedule_meeting'),
    meetingId: z.string(),
    slotId: z.string(),
  }),
  z.object({
    type: z.literal('reschedule_meeting'),
    meetingId: z.string(),
    newSlotId: z.string(),
  }),
  z.object({
    type: z.literal('cancel_meeting'),
    meetingId: z.string(),
  }),
  z.object({
    type: z.literal('skip'),
  }),
]);

export const RewardSchema = z.object({
  value: z.number(),
  components: z.record(z.string(), z.number()),
});

export type TimeSlot = z.infer<typeof TimeSlotSchema>;
export type Participant = z.infer<typeof ParticipantSchema>;
export type Meeting = z.infer<typeof MeetingSchema>;
export type Observation = z.infer<typeof ObservationSchema>;
export type Action = z.infer<typeof ActionSchema>;
export type Reward = z.infer<typeof RewardSchema>;
