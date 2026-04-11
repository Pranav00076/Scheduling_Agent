"""
Smart Scheduling Assistant — OpenEnv RL Challenge Inference Script
Ensures all LLM calls are routed through the LiteLLM proxy.
"""

import os
import json
import requests
import httpx
from typing import List, Optional
from openai import OpenAI

# ──────────────────────────────────────────────────────────────────────────────
# Required Environment Variables
# ──────────────────────────────────────────────────────────────────────────────

API_BASE_URL = os.environ["API_BASE_URL"]
API_KEY = os.environ["API_KEY"] or os.environ.get("HF_TOKEN")
MODEL_NAME = os.environ.get("MODEL_NAME")
ENV_BASE_URL = os.environ.get("ENV_BASE_URL", "http://localhost:3000")
TASK_NAME = os.environ.get("TASK_NAME", "easy")

BENCHMARK = "smart-scheduling-assistant"

# Initialize OpenAI client using LiteLLM proxy
client = OpenAI(
    base_url=API_BASE_URL,
    api_key=API_KEY
)

# Debug logs to verify proxy usage
print(f"[DEBUG] Using API_BASE_URL: {API_BASE_URL}", flush=True)
print(f"[DEBUG] Using MODEL_NAME: {MODEL_NAME}", flush=True)
print("Using LiteLLM Proxy:", os.environ["API_BASE_URL"], flush=True)

def test_llm_connection():
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[{"role": "user", "content": "Return JSON: {\"status\": \"ok\"}"}],
        response_format={"type": "json_object"}
    )
    print("[DEBUG] Proxy call successful:", response.choices[0].message.content, flush=True)
test_llm_connection()

# ──────────────────────────────────────────────────────────────────────────────
# Logging Functions (Required by OpenEnv)
# ──────────────────────────────────────────────────────────────────────────────

def log_start(task: str, env: str, model: str) -> None:
    print(f"[START] task={task} env={env} model={model}", flush=True)

def log_step(step: int, action: str, reward: float, done: bool, error: Optional[str]) -> None:
    error_val = error if error else "null"
    done_val = str(done).lower()
    print(
        f"[STEP] step={step} action={action} reward={reward:.2f} "
        f"done={done_val} error={error_val}",
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
# LLM Call Helper
# ──────────────────────────────────────────────────────────────────────────────

def get_llm_action(prompt: str) -> dict:
    """Call the LLM through the LiteLLM proxy."""
    response = client.chat.completions.create(
        model=MODEL_NAME,
        messages=[
            {
                "role": "system",
                "content": "You are an intelligent scheduling assistant. "
                           "Respond ONLY with a valid JSON object."
            },
            {"role": "user", "content": prompt}
        ],
        temperature=0,
    )

    content = response.choices[0].message.content.strip()

    # Remove markdown formatting if present
    if content.startswith("```json"):
        content = content[7:]
    if content.startswith("```"):
        content = content[3:]
    if content.endswith("```"):
        content = content[:-3]

    return json.loads(content.strip())

# ──────────────────────────────────────────────────────────────────────────────
# Inference Logic
# ──────────────────────────────────────────────────────────────────────────────

def run_inference(task_id: str = "easy"):
    log_start(task=task_id, env=BENCHMARK, model=MODEL_NAME)

    rewards: List[float] = []
    steps_taken = 0
    score = 0.0
    success = False

    try:
        # Reset Environment
        reset_response = requests.post(
            f"{ENV_BASE_URL}/reset",
            json={"taskId": task_id},
            timeout=30,
        )
        reset_response.raise_for_status()
        observation = reset_response.json()
        done = False

        while not done and steps_taken < 10:
            steps_taken += 1

            prompt = f"""
You are a smart scheduling assistant.

Current State:
{json.dumps(observation, indent=2)}

Available Actions:
1. {{"type": "schedule_meeting", "meetingId": "...", "slotId": "..."}}
2. {{"type": "reschedule_meeting", "meetingId": "...", "newSlotId": "..."}}
3. {{"type": "cancel_meeting", "meetingId": "..."}}
4. {{"type": "skip"}}

Respond ONLY with a valid JSON object.
"""

            error_msg: Optional[str] = None

            # Call LLM via LiteLLM proxy
            try:
                action = get_llm_action(prompt)
                action_str = json.dumps(action)
            except Exception as e:
                error_msg = str(e)
                print(f"[ERROR] LLM call failed: {error_msg}", flush=True)
                action = {"type": "skip"}
                action_str = json.dumps(action)

            # Step Environment
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
                reward_val = (
                    float(reward_data.get("value", 0.0))
                    if isinstance(reward_data, dict)
                    else float(reward_data)
                )

            except Exception as e:
                error_msg = str(e)
                reward_val = 0.0
                done = True

            rewards.append(reward_val)
            log_step(steps_taken, action_str, reward_val, done, error_msg)

        # Get Final Grade
        try:
            grade_response = requests.post(
                f"{ENV_BASE_URL}/grade",
                timeout=30,
            )
            grade_response.raise_for_status()
            score = float(grade_response.json().get("score", 0.0))
        except Exception as e:
            print(f"[ERROR] Grade fetch failed: {e}", flush=True)
            score = 0.0

        score = max(0.0, min(score, 1.0))
        success = score >= 0.1

    except Exception as e:
        print(f"[DEBUG] Unhandled exception: {e}", flush=True)

    finally:
        log_end(success, steps_taken, score, rewards)


# ──────────────────────────────────────────────────────────────────────────────
# Entry Point
# ──────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    run_inference(TASK_NAME)