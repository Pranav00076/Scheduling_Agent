import express from 'express';
import cors from 'cors';
import bodyParser from 'body-parser';
import { SchedulingEnvironment } from './src/env/environment';
import { ActionSchema } from './src/env/models';
import { gradeTask } from './src/env/grader';
import { getAllTasks } from './src/env/tasks';
import path from 'path';
import { createServer as createViteServer } from 'vite';
import { GoogleGenAI } from '@google/genai';

const app = express();
const PORT = 3000;

app.use(cors());
app.use(bodyParser.json());

const env = new SchedulingEnvironment();

// OpenEnv Endpoints
app.post('/reset', (req, res) => {
  const { taskId } = req.body;
  const observation = env.reset(taskId);
  res.json(observation);
});

app.post('/step', (req, res) => {
  try {
    const action = ActionSchema.parse(req.body.action);
    const [observation, reward, done, info] = env.step(action);
    res.json({ observation, reward, done, info });
  } catch (error) {
    res.status(400).json({ error: error instanceof Error ? error.message : 'Invalid action' });
  }
});

app.post('/ai-step', async (req, res) => {
  try {
    const { observation } = req.body;
    const apiKey = process.env.GEMINI_API_KEY;
    
    if (!apiKey || apiKey === 'MY_GEMINI_API_KEY' || apiKey === 'dummy') {
      return res.status(500).json({ 
        error: 'Please configure your Gemini API Key in the AI Studio Secrets panel. The current key is missing or invalid.' 
      });
    }

    const ai = new GoogleGenAI({ apiKey });
    
    const prompt = `
      You are an AI scheduling assistant playing a reinforcement learning environment.
      Your goal is to schedule all meetings into available slots without conflicts.
      
      Current State:
      Meetings to schedule: ${JSON.stringify(observation.meetings.filter((m: any) => !m.scheduledSlotId))}
      Available Calendar Slots: ${JSON.stringify(observation.calendar.filter((s: any) => s.isAvailable))}
      
      Available Actions:
      - {"type": "schedule_meeting", "meetingId": "...", "slotId": "..."}
      - {"type": "skip"}
      
      Pick ONE meeting and ONE available slot. 
      Respond ONLY with a valid JSON object representing your chosen action. Do not include markdown formatting.
    `;
    
    const response = await ai.models.generateContent({
      model: 'gemini-2.5-flash',
      contents: prompt,
    });
    
    const text = response.text;
    
    if (!text) {
      throw new Error('Empty response from Gemini');
    }
    
    // Extract JSON from response
    const jsonMatch = text.match(/\{[\s\S]*\}/);
    const action = JSON.parse(jsonMatch ? jsonMatch[0] : text);
    
    res.json({ action });
  } catch (error: any) {
    console.error('AI Error:', error);
    
    let errorMessage = 'Failed to generate AI action';
    
    if (error.message) {
      errorMessage = error.message;
      // Try to parse JSON error message from @google/genai
      try {
        if (errorMessage.includes('ApiError:')) {
          const jsonStr = errorMessage.split('ApiError:')[1].trim();
          const parsed = JSON.parse(jsonStr);
          if (parsed.error && parsed.error.message) {
            errorMessage = parsed.error.message;
          }
        }
      } catch (e) {
        // Ignore parsing errors
      }
    }
    
    res.status(500).json({ error: errorMessage });
  }
});

app.get('/state', (req, res) => {
  res.json(env.state());
});

app.get('/tasks', (req, res) => {
  res.json(getAllTasks());
});

app.post('/grade', (req, res) => {
  const state = env.state();
  const score = gradeTask(state);
  res.json({ score });
});

// Vite middleware for development
async function startServer() {
  if (process.env.NODE_ENV !== 'production') {
    const vite = await createViteServer({
      server: { middlewareMode: true },
      appType: 'spa',
    });
    app.use(vite.middlewares);
  } else {
    const distPath = path.join(process.cwd(), 'dist');
    app.use(express.static(distPath));
    app.get('*', (req, res) => {
      res.sendFile(path.join(distPath, 'index.html'));
    });
  }

  app.listen(PORT, '0.0.0.0', () => {
    console.log(`OpenEnv Server running on http://0.0.0.0:${PORT}`);
  });
}

startServer();
