"""
Smart Scheduling Assistant — OpenEnv RL Challenge Inference Script
This script interacts with the OpenEnv environment and makes decisions
using an LLM routed through the LiteLLM proxy.
"""

import os
import json
import requests
import httpx
from typing import List, Optional
from openai import OpenAI

# ──────────────────────────────────────────────────────────────────────────────
# Environment Variables (Injected by OpenEnv Validator)
# ──────────────────────────────────────────────────────────────────────────────

API_BASE_URL = os.getenv("API_BASE_URL")
API_KEY = os.getenv("API_KEY")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")

# Fallbacks for local development only
if not API_BASE_URL:
    API_BASE_URL = "https://router.huggingface.co/v1"

if not API_KEY:
    API_KEY = "sk-dummy-token-for-local-testing"

ENV_BASE_URL = os.getenv("ENV_BASE_URL", "http://localhost:3000")
TASK_NAME = os.getenv("TASK_NAME", "easy")
BENCHMARK = "smart-scheduling-assistant"

# ──────────────────────────────────────────────────────────────────────────────
# OpenAI Client Initialization
# ──────────────────────────────────────────────────────────────────────────────

http_client = httpx.Client(timeout=60.0)

client = OpenAI(
    base_url=API_BASE_URL,
    api_key=API_KEY,
    http_client=http_client
)

# ──────────────────────────────────────────────────────────────────────────────
# Logging Functions (Required by OpenEnv)
# ──────────────────────────────────────────────────────────────────────────────

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
    print(
        f"[END] success={str(success).lower()} steps={steps} "
        f"score={score:.3f} rewards={rewards_str}",
        flush=True,
    )

# ──────────────────────────────────────────────────────────────────────────────
# Helper Function to Call the LLM
# ──────────────────────────────────────────────────────────────────────────────

def get_llm_action(prompt: str) -> dict:
    """Calls the LLM via the LiteLLM proxy and returns a JSON action."""
    completion = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": "You are an intelligent scheduling assistant that outputs valid JSON."
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0,
    )

    response_text = completion.choices[0].message.content.strip()

    # Remove markdown formatting if present
    if response_text.startswith("```json"):
        response_text = response_text[7:]
    if response_text.startswith("```"):
        response_text = response_text[3:]
    if response_text.endswith("```"):
        response_text = response_text[:-3]

    response_text = response_text.strip()

    return json.loads(response_text)

# ──────────────────────────────────────────────────────────────────────────────
# Inference Logic
# ──────────────────────────────────────────────────────────────────────────────

def run_inference(task_id: str = "easy"):
    """Runs the agent for a specific task."""
    log_start(task=task_id, env=BENCHMARK, model=MODEL_NAME)

    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    try:
        # Reset environment
        response = requests.post(
            f"{ENV_BASE_URL}/reset",
            json={"taskId": task_id},
            timeout=30,
        )
        response.raise_for_status()
        observation = response.json()
        done = False

        while not done and steps_taken < 10:
            steps_taken += 1

            # Construct prompt
            prompt = f"""
You are a smart scheduling assistant.

Current State:
{json.dumps(observation, indent=2)}

Available Actions:
1. {{"type": "schedule_meeting", "meetingId": "...", "slotId": "..."}}
2. {{"type": "reschedule_meeting", "meetingId": "...", "newSlotId": "..."}}
3. {{"type": "cancel_meeting", "meetingId": "..."}}
4. {{"type": "skip"}}

Respond ONLY with a valid JSON object representing the best action.
"""

            error_msg: Optional[str] = None

            # Get action from LLM
            try:
                action = get_llm_action(prompt)
                action_str = json.dumps(action)
            except Exception as e:
                error_msg = str(e)
                # Fallback heuristic
                meeting = next(
                    (m for m in observation.get("meetings", [])
                     if not m.get("scheduledSlotId")),
                    None,
                )
                slot = next(
                    (s for s in observation.get("calendar", [])
                     if s.get("isAvailable")),
                    None,
                )

                if meeting and slot:
                    action = {
                        "type": "schedule_meeting",
                        "meetingId": meeting["id"],
                        "slotId": slot["id"],
                    }
                else:
                    action = {"type": "skip"}

                action_str = json.dumps(action)

            # Step environment
            try:
                step_response = requests.post(
                    f"{ENV_BASE_URL}/step",
                    json={"action": action},
                    timeout=30,
                )
                step_response.raise_for_status()
                step_data = step_response.json()

                observation = step_data.get("observation", observation)
                done = step_data.get("done", True)

                reward_data = step_data.get("reward", 0.0)
                if isinstance(reward_data, dict):
                    reward_val = float(reward_data.get("value", 0.0))
                else:
                    reward_val = float(reward_data)

            except Exception as e:
                error_msg = str(e)
                reward_val = 0.0
                done = True

            rewards.append(reward_val)

            log_step(
                step=steps_taken,
                action=action_str,
                reward=reward_val,
                done=done,
                error=error_msg,
            )

        # Get final grade
        try:
            grade_response = requests.post(
                f"{ENV_BASE_URL}/grade",
                timeout=30,
            )
            grade_response.raise_for_status()
            score = float(grade_response.json().get("score", 0.0))
        except Exception:
            score = 0.0

        score = max(0.0, min(score, 1.0))
        success = score >= 0.1

    except Exception as e:
        print(f"[DEBUG] Unhandled exception: {e}", flush=True)

    finally:
        log_end(
            success=success,
            steps=steps_taken,
            score=score,
            rewards=rewards,
        )

# ──────────────────────────────────────────────────────────────────────────────
# Entry Point
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    run_inference(TASK_NAME)