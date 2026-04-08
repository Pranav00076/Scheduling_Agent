from typing import Tuple, Any
from .models import Observation, Action, Reward, Meeting, TimeSlot, Participant
from .tasks import get_task
from .grader import calculate_reward

class SchedulingEnvironment:
    def __init__(self):
        self.meetings = []
        self.calendar = []
        self.participants = []
        self.current_step = 0
        self.max_steps = 50
        self.task_id = "easy"
        self.done = False

    def reset(self, task_id: str = "easy") -> Observation:
        task = get_task(task_id)
        self.task_id = task_id
        self.meetings = [m.copy(deep=True) for m in task.initialMeetings]
        self.calendar = [s.copy(deep=True) for s in task.initialCalendar]
        self.participants = [p.copy(deep=True) for p in task.initialParticipants]
        self.current_step = 0
        self.done = False
        return self._get_observation()

    def step(self, action: Action) -> Tuple[Observation, Reward, bool, Any]:
        if self.done:
            raise Exception("Environment is already done. Call reset().")

        self.current_step += 1
        reward = self._apply_action(action)

        if self.current_step >= self.max_steps or self._all_meetings_scheduled():
            self.done = True

        return self._get_observation(), reward, self.done, {"task_id": self.task_id}

    def state(self) -> Observation:
        return self._get_observation()

    def _get_observation(self) -> Observation:
        return Observation(
            calendar=self.calendar,
            meetings=self.meetings,
            participants=self.participants,
            currentStep=self.current_step,
            maxSteps=self.max_steps
        )

    def _apply_action(self, action: Action) -> Reward:
        components = {}
        
        if action.type == "schedule_meeting":
            meeting = next((m for m in self.meetings if m.id == action.meetingId), None)
            slot = next((s for s in self.calendar if s.id == action.slotId), None)

            if not meeting or not slot:
                components["error"] = -10.0
            elif meeting.scheduledSlotId:
                components["error"] = -5.0
            elif not slot.isAvailable:
                components["conflict"] = -10.0
            else:
                # Check participant availability
                unavailable = [p_id for p_id in meeting.participants 
                              if not any(p.id == p_id and slot.id in p.availability for p in self.participants)]
                
                if unavailable:
                    components["participant_conflict"] = -5.0 * len(unavailable)

                meeting.scheduledSlotId = slot.id
                slot.isAvailable = False
                components["scheduled"] = 10.0 * meeting.priority
                
                if slot.start <= meeting.deadline:
                    components["deadline_bonus"] = 5.0
                else:
                    components["deadline_penalty"] = -20.0

        elif action.type == "reschedule_meeting":
            meeting = next((m for m in self.meetings if m.id == action.meetingId), None)
            new_slot = next((s for s in self.calendar if s.id == action.newSlotId), None)

            if not meeting or not new_slot or not meeting.scheduledSlotId:
                components["error"] = -10.0
            elif not new_slot.isAvailable:
                components["conflict"] = -10.0
            else:
                old_slot = next((s for s in self.calendar if s.id == meeting.scheduledSlotId), None)
                if old_slot: old_slot.isAvailable = True
                meeting.scheduledSlotId = new_slot.id
                new_slot.isAvailable = False
                components["rescheduled"] = 2.0

        elif action.type == "cancel_meeting":
            meeting = next((m for m in self.meetings if m.id == action.meetingId), None)
            if meeting and meeting.scheduledSlotId:
                slot = next((s for s in self.calendar if s.id == meeting.scheduledSlotId), None)
                if slot: slot.isAvailable = True
                meeting.scheduledSlotId = None
                components["cancelled"] = -5.0

        elif action.type == "skip":
            components["skip"] = -1.0

        value = sum(components.values())
        return Reward(value=value, components=components)

    def _all_meetings_scheduled(self) -> bool:
        return all(m.scheduledSlotId is not None for m in self.meetings)
