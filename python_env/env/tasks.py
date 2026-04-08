from datetime import datetime, timedelta
from typing import List
from .models import Meeting, TimeSlot, Participant

class Task:
    def __init__(self, id: str, name: str, description: str, initialMeetings: List[Meeting], initialCalendar: List[TimeSlot], initialParticipants: List[Participant]):
        self.id = id
        self.name = name
        self.description = description
        self.initialMeetings = initialMeetings
        self.initialCalendar = initialCalendar
        self.initialParticipants = initialParticipants

def generate_time_slots(count: int) -> List[TimeSlot]:
    slots = []
    base_date = datetime(2026, 4, 10, 9, 0)
    for i in range(count):
        start = base_date + timedelta(hours=i)
        end = start + timedelta(hours=1)
        slots.append(TimeSlot(
            id=f"slot-{i}",
            start=start.isoformat() + "Z",
            end=end.isoformat() + "Z",
            isAvailable=True
        ))
    return slots

TASKS = {
    "easy": Task(
        id="easy",
        name="Simple Scheduling",
        description="Schedule 2 meetings with 2 participants. No conflicts.",
        initialCalendar=generate_time_slots(8),
        initialParticipants=[
            Participant(id="p1", name="Alice", availability=[f"slot-{i}" for i in range(5)]),
            Participant(id="p2", name="Bob", availability=[f"slot-{i}" for i in range(5)]),
        ],
        initialMeetings=[
            Meeting(id="m1", title="Sync", priority=5, durationMinutes=60, deadline="2026-04-10T17:00:00Z", participants=["p1", "p2"]),
            Meeting(id="m2", title="Review", priority=3, durationMinutes=60, deadline="2026-04-10T17:00:00Z", participants=["p1"]),
        ]
    ),
    "medium": Task(
        id="medium",
        name="Conflict Management",
        description="Schedule 4 meetings with overlapping availability.",
        initialCalendar=generate_time_slots(8),
        initialParticipants=[
            Participant(id="p1", name="Alice", availability=["slot-0", "slot-1", "slot-4"]),
            Participant(id="p2", name="Bob", availability=["slot-1", "slot-2", "slot-5"]),
            Participant(id="p3", name="Charlie", availability=["slot-0", "slot-2", "slot-6"]),
        ],
        initialMeetings=[
            Meeting(id="m1", title="Project A", priority=8, durationMinutes=60, deadline="2026-04-10T12:00:00Z", participants=["p1", "p2"]),
            Meeting(id="m2", title="Project B", priority=6, durationMinutes=60, deadline="2026-04-10T15:00:00Z", participants=["p2", "p3"]),
            Meeting(id="m3", title="Project C", priority=4, durationMinutes=60, deadline="2026-04-10T17:00:00Z", participants=["p1", "p3"]),
            Meeting(id="m4", title="1:1", priority=2, durationMinutes=60, deadline="2026-04-10T17:00:00Z", participants=["p1"]),
        ]
    ),
    "hard": Task(
        id="hard",
        name="Tight Deadlines",
        description="Many participants, very tight deadlines, and limited slots.",
        initialCalendar=generate_time_slots(6),
        initialParticipants=[
            Participant(id="p1", name="Alice", availability=["slot-0", "slot-1"]),
            Participant(id="p2", name="Bob", availability=["slot-1", "slot-2"]),
            Participant(id="p3", name="Charlie", availability=["slot-0", "slot-2"]),
            Participant(id="p4", name="Dave", availability=["slot-3", "slot-4"]),
        ],
        initialMeetings=[
            Meeting(id="m1", title="Critical Fix", priority=10, durationMinutes=60, deadline="2026-04-10T10:00:00Z", participants=["p1", "p2", "p3"]),
            Meeting(id="m2", title="Planning", priority=7, durationMinutes=60, deadline="2026-04-10T12:00:00Z", participants=["p1", "p4"]),
            Meeting(id="m3", title="Review", priority=5, durationMinutes=60, deadline="2026-04-10T14:00:00Z", participants=["p2", "p4"]),
            Meeting(id="m4", title="Retro", priority=3, durationMinutes=60, deadline="2026-04-10T16:00:00Z", participants=["p3", "p4"]),
        ]
    )
}

def get_task(id: str) -> Task:
    return TASKS.get(id, TASKS["easy"])

def get_all_tasks() -> List[Task]:
    return list(TASKS.values())
