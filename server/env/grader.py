from .models import Observation

EPSILON = 1e-3  # Ensures scores stay strictly within (0, 1)

def calculate_reward(observation: Observation) -> float:
    meetings = observation.meetings
    calendar = observation.calendar
    participants = observation.participants

    if not meetings:
        return EPSILON

    score = 0.0
    max_possible_score = sum(float(m.priority) for m in meetings)

    if max_possible_score == 0:
        return EPSILON

    for meeting in meetings:
        if meeting.scheduledSlotId:
            slot = next(
                (s for s in calendar if s.id == meeting.scheduledSlotId),
                None
            )
            if not slot:
                continue

            meeting_score = float(meeting.priority)

            # Penalty for missing deadline
            if slot.start > meeting.deadline:
                meeting_score *= 0.2

            # Penalty for participant conflicts
            unavailable_count = 0
            for p_id in meeting.participants:
                participant = next(
                    (p for p in participants if p.id == p_id),
                    None
                )
                if participant and slot.id not in participant.availability:
                    unavailable_count += 1

            if unavailable_count > 0:
                meeting_score *= 0.5

            score += meeting_score

    normalized_score = score / max_possible_score

    # Clamp strictly within (0, 1)
    normalized_score = max(EPSILON, min(1.0 - EPSILON, normalized_score))
    return float(normalized_score)


def grade_task(observation: Observation) -> float:
    return calculate_reward(observation)