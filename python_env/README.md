---
title: Smart Scheduling Agent
emoji: 📅
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
app_file: app.py
---

# Smart Scheduling Assistant Environment

An OpenEnv-compliant environment for training and evaluating AI agents on meeting scheduling tasks.

## Environment Description

The environment simulates a scheduling assistant that must manage multiple participants' calendars, meeting priorities, and deadlines.

## Action Space

- `schedule_meeting(meetingId, slotId)`: Assign a meeting to a specific time slot.
- `reschedule_meeting(meetingId, newSlotId)`: Move an already scheduled meeting.
- `cancel_meeting(meetingId)`: Remove a meeting from the schedule.
- `skip()`: Do nothing for the current step.

## Observation Space

- `calendar`: List of time slots with availability status.
- `meetings`: List of meetings to be scheduled with priorities and deadlines.
- `participants`: List of participants and their specific availability.
- `currentStep`: Current step in the episode.
- `maxSteps`: Maximum steps allowed.

## Tasks

1. **Easy**: 2 meetings, 2 participants, no conflicts.
2. **Medium**: 4 meetings, 3 participants, overlapping availability.
3. **Hard**: 4 meetings, 4 participants, tight deadlines, limited slots.

## Setup Instructions

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the server:
   ```bash
   uvicorn app:app --host 0.0.0.0 --port 3000
   ```

## Example Usage

See `inference.py` for a baseline implementation using an OpenAI-compatible client.
