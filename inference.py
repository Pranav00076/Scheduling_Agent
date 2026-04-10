import os
import json
import requests
import httpx
from typing import List, Optional
from openai import OpenAI

# Required environment variables
HF_TOKEN = os.getenv("HF_TOKEN") or os.getenv("API_KEY")
API_BASE_URL = os.getenv("API_BASE_URL") or "https://router.huggingface.co/v1"
MODEL_NAME = os.getenv("MODEL_NAME") or "Qwen/Qwen2.5-72B-Instruct"

ENV_BASE_URL = os.getenv("ENV_BASE_URL", "http://localhost:3000")
TASK_NAME = os.getenv("TASK_NAME", "easy")
BENCHMARK = "smart-scheduling-assistant"

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} done={done_val} error={error_val}",
        flush=True,
    )

def log_end(success: bool, steps: int, score: float, rewards: List[float]) -> None:
    rewards_str = ",".join(f"{r:.2f}" for r in rewards)
    print(f"[END] success={str(success).lower()} steps={steps} score={score:.3f} rewards={rewards_str}", flush=True)

def run_inference(task_id="easy"):
    client = OpenAI(
        base_url=API_BASE_URL,
        api_key=HF_TOKEN
    )

    log_start(task=task_id, env=BENCHMARK, model=MODEL_NAME)
    
    rewards = []
    steps_taken = 0
    score = 0.0
    success = False

    try:
        # 1. Reset
        response = requests.post(f"{ENV_BASE_URL}/reset", json={"taskId": task_id})
        response.raise_for_status()
        observation = response.json()
        done = False
        
        while not done and steps_taken < 10:
            steps_taken += 1
            
            # 2. Agent decides
            prompt = f"""
            You are a scheduling assistant. 
            Current State: {json.dumps(observation)}
            
            Available Actions:
            - {{"type": "schedule_meeting", "meetingId": "...", "slotId": "..."}}
            - {{"type": "reschedule_meeting", "meetingId": "...", "newSlotId": "..."}}
            - {{"type": "cancel_meeting", "meetingId": "..."}}
            - {{"type": "skip"}}
            
            Respond with ONLY a JSON object.
            """
            
            action = None
            action_str = ""
            error_msg = None
            
            try:
                completion = client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[{"role": "user", "content": prompt}]
                )
                response_text = completion.choices[0].message.content.strip()
                
                # Strip markdown code blocks if present
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                if response_text.startswith("```"):
                    response_text = response_text[3:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]
                response_text = response_text.strip()
                
                action = json.loads(response_text)
                action_str = json.dumps(action)
            except Exception as e:
                print(f"[DEBUG] LLM call or parsing failed: {e}", flush=True)
                error_msg = str(e)
                # Fallback to a valid action if LLM fails
                meeting = next((m for m in observation.get('meetings', []) if not m.get('scheduledSlotId')), None)
                slot = next((s for s in observation.get('calendar', []) if s.get('isAvailable')), None)
                if meeting and slot:
                    action = {"type": "schedule_meeting", "meetingId": meeting['id'], "slotId": slot['id']}
                else:
                    action = {"type": "skip"}
                action_str = json.dumps(action)

            # 3. Step Environment
            try:
                step_response = requests.post(f"{ENV_BASE_URL}/step", json={"action": action})
                step_response.raise_for_status()
                step_data = step_response.json()
                
                observation = step_data.get('observation', observation)
                done = step_data.get('done', True)
                
                # Handle reward which might be an object or a float
                reward_data = step_data.get('reward', 0.0)
                if isinstance(reward_data, dict):
                    reward_val = float(reward_data.get('value', 0.0))
                else:
                    reward_val = float(reward_data)
                    
            except Exception as e:
                error_msg = str(e)
                reward_val = 0.0
                done = True
                
            rewards.append(reward_val)
            log_step(step=steps_taken, action=action_str, reward=reward_val, done=done, error=error_msg)

        # 4. Final Grade
        try:
            grade_response = requests.post(f"{ENV_BASE_URL}/grade")
            grade_response.raise_for_status()
            score = float(grade_response.json().get('score', 0.0))
        except Exception as e:
            print(f"[DEBUG] Failed to get grade: {e}")
            score = 0.0
            
        # Clamp score to [0, 1]
        score = min(max(score, 0.0), 1.0)
        success = score >= 0.1

    except Exception as e:
        print(f"[DEBUG] Unhandled exception during inference: {e}")
        
    finally:
        log_end(success=success, steps=steps_taken, score=score, rewards=rewards)

if __name__ == "__main__":
    run_inference("easy")
