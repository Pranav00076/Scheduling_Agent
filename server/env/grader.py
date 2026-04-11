from .models import Observation

def calculate_reward(observation: Observation) -> float:
    meetings = observation.meetings
    calendar = observation.calendar
    participants = observation.participants
    
    if not meetings:
        return 0.01

    score = 0.01
    max_possible_score = sum(m.priority for m in meetings)

    for meeting in meetings:
        if meeting.scheduledSlotId:
            slot = next((s for s in calendar if s.id == meeting.scheduledSlotId), None)
            if slot:
                meeting_score = float(meeting.priority)

                # Penalty for missing deadline
                if slot.start > meeting.deadline:
                    meeting_score *= 0.2

                # Penalty for participant conflicts
                unavailable_count = 0
                for p_id in meeting.participants:
                    p = next((part for part in participants if part.id == p_id), None)
                    if p and slot.id not in p.availability:
                        unavailable_count += 1
                
                if unavailable_count > 0:
                    meeting_score *= 0.5

                score += meeting_score

    return max(0.01, min(0.99, score / max_possible_score))

def grade_task(observation: Observation) -> float:
    return calculate_reward(observation)
