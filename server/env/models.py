from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Union, Literal

class TimeSlot(BaseModel):
    id: str
    start: str
    end: str
    isAvailable: bool

class Participant(BaseModel):
    id: str
    name: str
    availability: List[str]

class Meeting(BaseModel):
    id: str
    title: str
    priority: int = Field(ge=1, le=10)
    durationMinutes: int
    deadline: str
    participants: List[str]
    scheduledSlotId: Optional[str] = None

class Observation(BaseModel):
    calendar: List[TimeSlot]
    meetings: List[Meeting]
    participants: List[Participant]
    currentStep: int
    maxSteps: int

class Action(BaseModel):
    type: Literal["schedule_meeting", "reschedule_meeting", "cancel_meeting", "skip"]
    meetingId: Optional[str] = None
    slotId: Optional[str] = None
    newSlotId: Optional[str] = None

class Reward(BaseModel):
    value: float
    components: Dict[str, float]
