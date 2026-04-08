import { Meeting, TimeSlot, Participant } from './models';

export interface Task {
  id: string;
  name: string;
  description: string;
  initialMeetings: Meeting[];
  initialCalendar: TimeSlot[];
  initialParticipants: Participant[];
}

const generateTimeSlots = (count: number): TimeSlot[] => {
  const slots: TimeSlot[] = [];
  const baseDate = new Date('2026-04-10T09:00:00Z');
  for (let i = 0; i < count; i++) {
    const start = new Date(baseDate.getTime() + i * 3600000); // 1 hour intervals
    const end = new Date(start.getTime() + 3600000);
    slots.push({
      id: `slot-${i}`,
      start: start.toISOString(),
      end: end.toISOString(),
      isAvailable: true,
    });
  }
  return slots;
};

const TASKS: Record<string, Task> = {
  easy: {
    id: 'easy',
    name: 'Simple Scheduling',
    description: 'Schedule 2 meetings with 2 participants. No conflicts.',
    initialCalendar: generateTimeSlots(8),
    initialParticipants: [
      { id: 'p1', name: 'Alice', availability: ['slot-0', 'slot-1', 'slot-2', 'slot-3', 'slot-4'] },
      { id: 'p2', name: 'Bob', availability: ['slot-0', 'slot-1', 'slot-2', 'slot-3', 'slot-4'] },
    ],
    initialMeetings: [
      {
        id: 'm1',
        title: 'Sync',
        priority: 5,
        durationMinutes: 60,
        deadline: '2026-04-10T17:00:00Z',
        participants: ['p1', 'p2'],
      },
      {
        id: 'm2',
        title: 'Review',
        priority: 3,
        durationMinutes: 60,
        deadline: '2026-04-10T17:00:00Z',
        participants: ['p1'],
      },
    ],
  },
  medium: {
    id: 'medium',
    name: 'Conflict Management',
    description: 'Schedule 4 meetings with overlapping availability.',
    initialCalendar: generateTimeSlots(8),
    initialParticipants: [
      { id: 'p1', name: 'Alice', availability: ['slot-0', 'slot-1', 'slot-4'] },
      { id: 'p2', name: 'Bob', availability: ['slot-1', 'slot-2', 'slot-5'] },
      { id: 'p3', name: 'Charlie', availability: ['slot-0', 'slot-2', 'slot-6'] },
    ],
    initialMeetings: [
      { id: 'm1', title: 'Project A', priority: 8, durationMinutes: 60, deadline: '2026-04-10T12:00:00Z', participants: ['p1', 'p2'] },
      { id: 'm2', title: 'Project B', priority: 6, durationMinutes: 60, deadline: '2026-04-10T15:00:00Z', participants: ['p2', 'p3'] },
      { id: 'm3', title: 'Project C', priority: 4, durationMinutes: 60, deadline: '2026-04-10T17:00:00Z', participants: ['p1', 'p3'] },
      { id: 'm4', title: '1:1', priority: 2, durationMinutes: 60, deadline: '2026-04-10T17:00:00Z', participants: ['p1'] },
    ],
  },
  hard: {
    id: 'hard',
    name: 'Tight Deadlines',
    description: 'Many participants, very tight deadlines, and limited slots.',
    initialCalendar: generateTimeSlots(6),
    initialParticipants: [
      { id: 'p1', name: 'Alice', availability: ['slot-0', 'slot-1'] },
      { id: 'p2', name: 'Bob', availability: ['slot-1', 'slot-2'] },
      { id: 'p3', name: 'Charlie', availability: ['slot-0', 'slot-2'] },
      { id: 'p4', name: 'Dave', availability: ['slot-3', 'slot-4'] },
    ],
    initialMeetings: [
      { id: 'm1', title: 'Critical Fix', priority: 10, durationMinutes: 60, deadline: '2026-04-10T10:00:00Z', participants: ['p1', 'p2', 'p3'] },
      { id: 'm2', title: 'Planning', priority: 7, durationMinutes: 60, deadline: '2026-04-10T12:00:00Z', participants: ['p1', 'p4'] },
      { id: 'm3', title: 'Review', priority: 5, durationMinutes: 60, deadline: '2026-04-10T14:00:00Z', participants: ['p2', 'p4'] },
      { id: 'm4', title: 'Retro', priority: 3, durationMinutes: 60, deadline: '2026-04-10T16:00:00Z', participants: ['p3', 'p4'] },
    ],
  },
};

export const getTask = (id: string): Task => {
  return TASKS[id] || TASKS['easy'];
};

export const getAllTasks = (): Task[] => {
  return Object.values(TASKS);
};
