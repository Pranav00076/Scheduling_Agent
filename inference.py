import os
import json
import requests
from openai import OpenAI

# API_BASE_URL is the API endpoint for the LLM as per the checklist
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4-turbo")
HF_TOKEN = os.getenv("HF_TOKEN", "dummy")

# ENV_BASE_URL is the endpoint for the local environment
ENV_BASE_URL = os.getenv("ENV_BASE_URL", "http://localhost:3000")

# Initialize OpenAI client as required by the checklist
client = OpenAI(
    base_url=API_BASE_URL,
    api_key=HF_TOKEN
)

def run_inference(task_id="easy"):
    print("[START]")
    
    # 1. Reset
    response = requests.post(f"{ENV_BASE_URL}/reset", json={"taskId": task_id})
    observation = response.json()
    done = False
    step_count = 0

    while not done and step_count < 10:
        print(f"[STEP {step_count}]")
        
        # 2. Agent decides
        prompt = f"""
        You are a scheduling assistant. 
        Current State: {json.dumps(observation)}
        
        Available Actions:
        - {{"type": "schedule_meeting", "meetingId": "...", "slotId": "..."}}
        - {{"type": "reschedule_meeting", "meetingId": "...", "newSlotId": "..."}}
        - {{"type": "cancel_meeting", "meetingId": "..."}}
        - {{"type": "skip"}}
        
        Respond with a JSON object.
        """
        
        try:
            # We use the OpenAI client as required by the checklist
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"}
            )
            response_text = completion.choices[0].message.content
            action = json.loads(response_text)
        except Exception as e:
            # Fallback to a valid action if LLM fails or is not configured
            meeting = next((m for m in observation['meetings'] if not m.get('scheduledSlotId')), None)
            slot = next((s for s in observation['calendar'] if s.get('isAvailable')), None)
            if meeting and slot:
                action = {"type": "schedule_meeting", "meetingId": meeting['id'], "slotId": slot['id']}
            else:
                action = {"type": "skip"}

        # 3. Step Environment
        step_response = requests.post(f"{ENV_BASE_URL}/step", json={"action": action})
        step_data = step_response.json()
        observation = step_data['observation']
        done = step_data['done']
        
        print(f"Action: {action.get('type')}, Reward: {step_data['reward']['value']}")
        step_count += 1

    # 4. Final Grade
    grade_response = requests.post(f"{ENV_BASE_URL}/grade")
    print(f"Final Score: {grade_response.json()['score']}")
    print("[END]")

if __name__ == "__main__":
    run_inference("easy")
