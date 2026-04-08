import os
import json
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Any, Dict
from env.environment import SchedulingEnvironment
from env.models import Action, Observation, Reward
from env.grader import grade_task
from env.tasks import get_all_tasks

try:
    from google import genai
    from google.genai import types
    GENAI_AVAILABLE = True
except ImportError:
    GENAI_AVAILABLE = False

app = FastAPI(title="Smart Scheduling Assistant Environment")
env = SchedulingEnvironment()

class ResetRequest(BaseModel):
    taskId: Optional[str] = "easy"

class StepRequest(BaseModel):
    action: Action

class AiStepRequest(BaseModel):
    observation: Dict[str, Any]

@app.post("/reset", response_model=Observation)
async def reset(request: Optional[ResetRequest] = None):
    task_id = request.taskId if request else "easy"
    return env.reset(task_id)

@app.post("/step")
async def step(request: StepRequest):
    try:
        observation, reward, done, info = env.step(request.action)
        return {"observation": observation, "reward": reward, "done": done, "info": info}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/ai-step")
async def ai_step(request: AiStepRequest):
    if not GENAI_AVAILABLE:
        raise HTTPException(status_code=500, detail="google-genai package is not installed. Please run: pip install google-genai")
        
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key or api_key == "MY_GEMINI_API_KEY" or api_key == "dummy":
        raise HTTPException(status_code=500, detail="Please configure your Gemini API Key in the environment variables.")
        
    try:
        client = genai.Client(api_key=api_key)
        
        obs = request.observation
        unscheduled = [m for m in obs.get("meetings", []) if not m.get("scheduledSlotId")]
        available_slots = [s for s in obs.get("calendar", []) if s.get("isAvailable")]
        
        prompt = f"""
        You are an AI scheduling assistant playing a reinforcement learning environment.
        Your goal is to schedule all meetings into available slots without conflicts.
        
        Current State:
        Meetings to schedule: {json.dumps(unscheduled)}
        Available Calendar Slots: {json.dumps(available_slots)}
        
        Available Actions:
        - {{"type": "schedule_meeting", "meetingId": "...", "slotId": "..."}}
        - {{"type": "skip"}}
        
        Pick ONE meeting and ONE available slot. 
        Respond ONLY with a valid JSON object representing your chosen action. Do not include markdown formatting.
        """
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
        )
        
        text = response.text
        if not text:
            raise ValueError("Empty response from Gemini")
            
        # Extract JSON from response
        import re
        json_match = re.search(r'\{[\s\S]*\}', text)
        action = json.loads(json_match.group(0) if json_match else text)
        
        return {"action": action}
    except Exception as e:
        print(f"AI Error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to generate AI action: {str(e)}")

@app.get("/state", response_model=Observation)
async def state():
    return env.state()

@app.get("/tasks")
async def tasks():
    return get_all_tasks()

@app.post("/grade")
async def grade():
    current_state = env.state()
    score = grade_task(current_state)
    return {"score": score}

# Serve the React frontend
dist_path = os.path.join(os.path.dirname(__file__), "dist")
if os.path.exists(dist_path):
    from fastapi.responses import RedirectResponse
    
    @app.get("/web")
    async def web_redirect():
        return RedirectResponse(url="/")
        
    app.mount("/", StaticFiles(directory=dist_path, html=True), name="web")
else:
    @app.get("/")
    async def root():
        return {"message": "API is running. Build the frontend and place it in the 'dist' directory to serve the UI."}
    
    @app.get("/web")
    async def web_redirect():
        return {"message": "UI not built."}

if __name__ == "__main__":
    import uvicorn
    # Hugging Face Spaces typically uses port 7860
    port = int(os.environ.get("PORT", 3000))
    uvicorn.run(app, host="0.0.0.0", port=port)
