import { Observation, Reward, Meeting, TimeSlot } from './models';

export const calculateReward = (observation: Observation): number => {
  // This is used for the final score [0.0, 1.0]
  const { meetings, calendar } = observation;
  
  if (meetings.length === 0) return 0;

  let score = 0;
  const maxPossibleScore = meetings.reduce((acc, m) => acc + m.priority, 0);

  meetings.forEach(meeting => {
    if (meeting.scheduledSlotId) {
      const slot = calendar.find(s => s.id === meeting.scheduledSlotId);
      if (slot) {
        // Base score: priority
        let meetingScore = meeting.priority;

        // Penalty for missing deadline
        if (new Date(slot.start) > new Date(meeting.deadline)) {
          meetingScore *= 0.2; // 80% penalty
        }

        // Penalty for participant conflicts (should be handled by env, but double check)
        const unavailableCount = meeting.participants.filter(pId => {
          const p = observation.participants.find(part => part.id === pId);
          return p && !p.availability.includes(slot.id);
        }).length;

        if (unavailableCount > 0) {
          meetingScore *= 0.5; // 50% penalty
        }

        score += meetingScore;
      }
    }
  });

  return Math.max(0, Math.min(1, score / maxPossibleScore));
};

export const gradeTask = (observation: Observation): number => {
  return calculateReward(observation);
};
