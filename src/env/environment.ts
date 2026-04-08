import { Observation, Action, Reward, Meeting, TimeSlot, Participant } from './models';
import { Task, getTask } from './tasks';
import { calculateReward } from './grader';

export class SchedulingEnvironment {
  private meetings: Meeting[] = [];
  private calendar: TimeSlot[] = [];
  private participants: Participant[] = [];
  private currentStep: number = 0;
  private maxSteps: number = 50;
  private taskId: string = 'easy';
  private done: boolean = false;

  constructor() {}

  public reset(taskId: string = 'easy'): Observation {
    const task = getTask(taskId);
    this.taskId = taskId;
    this.meetings = JSON.parse(JSON.stringify(task.initialMeetings));
    this.calendar = JSON.parse(JSON.stringify(task.initialCalendar));
    this.participants = JSON.parse(JSON.stringify(task.initialParticipants));
    this.currentStep = 0;
    this.done = false;
    return this.getObservation();
  }

  public step(action: Action): [Observation, Reward, boolean, any] {
    if (this.done) {
      throw new Error('Environment is already done. Call reset().');
    }

    this.currentStep++;
    const reward = this.applyAction(action);

    if (this.currentStep >= this.maxSteps || this.allMeetingsScheduled()) {
      this.done = true;
    }

    return [this.getObservation(), reward, this.done, { taskId: this.taskId }];
  }

  public state(): Observation {
    return this.getObservation();
  }

  private getObservation(): Observation {
    return {
      calendar: this.calendar,
      meetings: this.meetings,
      participants: this.participants,
      currentStep: this.currentStep,
      maxSteps: this.maxSteps,
    };
  }

  private applyAction(action: Action): Reward {
    let value = 0;
    const components: Record<string, number> = {};

    switch (action.type) {
      case 'schedule_meeting': {
        const meeting = this.meetings.find(m => m.id === action.meetingId);
        const slot = this.calendar.find(s => s.id === action.slotId);

        if (!meeting || !slot) {
          components['error'] = -10;
          break;
        }

        if (meeting.scheduledSlotId) {
          components['error'] = -5; // Already scheduled
          break;
        }

        if (!slot.isAvailable) {
          components['conflict'] = -10;
          break;
        }

        // Check participant availability
        const unavailableParticipants = meeting.participants.filter(pId => {
          const p = this.participants.find(part => part.id === pId);
          return p && !p.availability.includes(slot.id);
        });

        if (unavailableParticipants.length > 0) {
          components['participant_conflict'] = -5 * unavailableParticipants.length;
        }

        // Schedule it
        meeting.scheduledSlotId = slot.id;
        slot.isAvailable = false;

        components['scheduled'] = 10 * meeting.priority;
        
        // Bonus for meeting deadline
        if (new Date(slot.start) <= new Date(meeting.deadline)) {
          components['deadline_bonus'] = 5;
        } else {
          components['deadline_penalty'] = -20;
        }
        break;
      }

      case 'reschedule_meeting': {
        const meeting = this.meetings.find(m => m.id === action.meetingId);
        const oldSlotId = meeting?.scheduledSlotId;
        const newSlot = this.calendar.find(s => s.id === action.newSlotId);

        if (!meeting || !newSlot || !oldSlotId) {
          components['error'] = -10;
          break;
        }

        if (!newSlot.isAvailable) {
          components['conflict'] = -10;
          break;
        }

        // Free old slot
        const oldSlot = this.calendar.find(s => s.id === oldSlotId);
        if (oldSlot) oldSlot.isAvailable = true;

        // Schedule new slot
        meeting.scheduledSlotId = newSlot.id;
        newSlot.isAvailable = false;

        components['rescheduled'] = 2;
        break;
      }

      case 'cancel_meeting': {
        const meeting = this.meetings.find(m => m.id === action.meetingId);
        if (meeting && meeting.scheduledSlotId) {
          const slot = this.calendar.find(s => s.id === meeting.scheduledSlotId);
          if (slot) slot.isAvailable = true;
          meeting.scheduledSlotId = undefined;
          components['cancelled'] = -5;
        }
        break;
      }

      case 'skip':
        components['skip'] = -1;
        break;
    }

    value = Object.values(components).reduce((a, b) => a + b, 0);
    return { value, components };
  }

  private allMeetingsScheduled(): boolean {
    return this.meetings.every(m => !!m.scheduledSlotId);
  }
}
