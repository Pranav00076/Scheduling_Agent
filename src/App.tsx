import React, { useState, useEffect } from 'react';
import { Calendar, Users, Clock, CheckCircle2, AlertCircle, Play, RotateCcw, ChevronRight, Bot } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';
import axios from 'axios';

const API_BASE_URL = ''; // Relative path to hit the same host

export default function App() {
  const [observation, setObservation] = useState<any>(null);
  const [taskId, setTaskId] = useState('easy');
  const [reward, setReward] = useState<any>(null);
  const [done, setDone] = useState(false);
  const [loading, setLoading] = useState(false);
  const [score, setScore] = useState<number | null>(null);
  const [aiThinking, setAiThinking] = useState(false);

  const reset = async (id: string = taskId) => {
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE_URL}/reset`, { taskId: id });
      setObservation(res.data);
      setReward(null);
      setDone(false);
      setScore(null);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const step = async (action: any) => {
    if (done) return;
    setLoading(true);
    try {
      const res = await axios.post(`${API_BASE_URL}/step`, { action });
      setObservation(res.data.observation);
      setReward(res.data.reward);
      setDone(res.data.done);
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const runAIAgent = async () => {
    if (done || !observation) return;
    setAiThinking(true);
    try {
      const res = await axios.post(`${API_BASE_URL}/ai-step`, { observation });
      const action = res.data.action;
      await step(action);
    } catch (err: any) {
      console.error("AI Agent Error:", err);
      let errorMessage = "Unknown error occurred";
      if (err.response?.data) {
        if (typeof err.response.data === 'string') {
          // If it's an HTML page (e.g. from Hugging Face router), show a snippet
          errorMessage = err.response.data.substring(0, 100) + "...";
        } else {
          errorMessage = err.response.data.detail || err.response.data.error || JSON.stringify(err.response.data);
        }
      } else if (err.message) {
        errorMessage = err.message;
      }
      alert(`AI Agent Error: ${errorMessage}`);
    }
    setAiThinking(false);
  };

  const grade = async () => {
    try {
      const res = await axios.post(`${API_BASE_URL}/grade`);
      setScore(res.data.score);
    } catch (err) {
      console.error(err);
    }
  };

  useEffect(() => {
    reset();
  }, []);

  if (!observation) return <div className="flex items-center justify-center h-screen bg-slate-950 text-white">Loading Environment...</div>;

  return (
    <div className="min-h-screen bg-slate-950 text-slate-200 p-6 font-sans">
      <header className="max-w-7xl mx-auto mb-8 flex justify-between items-end">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Smart Scheduling Assistant</h1>
          <p className="text-slate-400 mt-1">OpenEnv-compliant RL Environment</p>
        </div>
        <div className="flex gap-3">
          <select 
            value={taskId} 
            onChange={(e) => {
              setTaskId(e.target.value);
              reset(e.target.value);
            }}
            className="bg-slate-900 border border-slate-800 rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="easy">Easy Task</option>
            <option value="medium">Medium Task</option>
            <option value="hard">Hard Task</option>
          </select>
          
          <button 
            onClick={runAIAgent}
            disabled={done || aiThinking}
            className="flex items-center gap-2 bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 disabled:opacity-50 text-white px-4 py-2 rounded-lg transition-colors text-sm font-medium"
          >
            <Bot size={16} /> {aiThinking ? 'AI is thinking...' : 'Ask AI to take 1 step'}
          </button>

          <button 
            onClick={() => reset()}
            className="flex items-center gap-2 bg-slate-800 hover:bg-slate-700 text-white px-4 py-2 rounded-lg transition-colors text-sm font-medium"
          >
            <RotateCcw size={16} /> Reset
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left Column: Calendar & Participants */}
        <div className="lg:col-span-8 space-y-6">
          {/* Calendar Grid */}
          <section className="bg-slate-900/50 border border-slate-800 rounded-xl p-6">
            <div className="flex items-center gap-2 mb-4 text-white font-semibold">
              <Calendar size={20} className="text-blue-400" />
              <h2>Calendar Slots</h2>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              {observation.calendar.map((slot: any) => (
                <div 
                  key={slot.id}
                  className={`p-3 rounded-lg border transition-all ${
                    slot.isAvailable 
                      ? 'bg-slate-900 border-slate-800 hover:border-blue-500/50' 
                      : 'bg-blue-500/10 border-blue-500/30'
                  }`}
                >
                  <div className="text-xs text-slate-500 mb-1">{new Date(slot.start).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</div>
                  <div className="text-sm font-medium truncate">
                    {slot.isAvailable ? 'Available' : 'Booked'}
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Participants */}
          <section className="bg-slate-900/50 border border-slate-800 rounded-xl p-6">
            <div className="flex items-center gap-2 mb-4 text-white font-semibold">
              <Users size={20} className="text-purple-400" />
              <h2>Participants</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {observation.participants.map((p: any) => (
                <div key={p.id} className="bg-slate-900 border border-slate-800 rounded-lg p-3">
                  <div className="font-medium text-white mb-2">{p.name}</div>
                  <div className="flex flex-wrap gap-1">
                    {p.availability.map((sId: string) => (
                      <span key={sId} className="text-[10px] bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded">
                        {sId.split('-')[1]}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>

        {/* Right Column: Meetings & Actions */}
        <div className="lg:col-span-4 space-y-6">
          {/* Meetings List */}
          <section className="bg-slate-900/50 border border-slate-800 rounded-xl p-6">
            <div className="flex items-center gap-2 mb-4 text-white font-semibold">
              <Clock size={20} className="text-amber-400" />
              <h2>Meetings to Schedule</h2>
            </div>
            <div className="space-y-3">
              {observation.meetings.map((m: any) => (
                <div 
                  key={m.id}
                  className={`p-4 rounded-lg border transition-all ${
                    m.scheduledSlotId 
                      ? 'bg-emerald-500/10 border-emerald-500/30' 
                      : 'bg-slate-900 border-slate-800'
                  }`}
                >
                  <div className="flex justify-between items-start mb-2">
                    <h3 className="font-medium text-white">{m.title}</h3>
                    <span className="text-[10px] bg-slate-800 text-slate-400 px-2 py-0.5 rounded-full uppercase tracking-wider font-bold">
                      P{m.priority}
                    </span>
                  </div>
                  <div className="text-xs text-slate-500 space-y-1">
                    <div className="flex items-center gap-1">
                      <Users size={12} /> {m.participants.join(', ')}
                    </div>
                    <div className="flex items-center gap-1">
                      <AlertCircle size={12} /> {new Date(m.deadline).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </div>
                  </div>
                  {!m.scheduledSlotId && !done && (
                    <div className="mt-3 flex flex-wrap gap-2">
                      {observation.calendar.filter((s: any) => s.isAvailable).slice(0, 3).map((s: any) => (
                        <button
                          key={s.id}
                          onClick={() => step({ type: 'schedule_meeting', meetingId: m.id, slotId: s.id })}
                          className="text-[10px] bg-blue-600 hover:bg-blue-500 text-white px-2 py-1 rounded transition-colors"
                        >
                          Slot {s.id.split('-')[1]}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </section>

          {/* Status & Reward */}
          <section className="bg-slate-900 border border-slate-800 rounded-xl p-6">
            <div className="flex justify-between items-center mb-6">
              <div>
                <div className="text-xs text-slate-500 uppercase font-bold tracking-widest mb-1">Step</div>
                <div className="text-2xl font-mono text-white">{observation.currentStep} / {observation.maxSteps}</div>
              </div>
              <div className="text-right">
                <div className="text-xs text-slate-500 uppercase font-bold tracking-widest mb-1">Status</div>
                <div className={`text-sm font-bold ${done ? 'text-emerald-400' : 'text-blue-400'}`}>
                  {done ? 'COMPLETED' : 'IN PROGRESS'}
                </div>
              </div>
            </div>

            {reward && (
              <motion.div 
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-slate-950 rounded-lg p-4 mb-6 border border-slate-800"
              >
                <div className="text-xs text-slate-500 mb-2">Last Reward</div>
                <div className={`text-3xl font-bold ${reward.value >= 0 ? 'text-emerald-400' : 'text-rose-400'}`}>
                  {reward.value > 0 ? '+' : ''}{reward.value}
                </div>
                <div className="mt-2 space-y-1">
                  {Object.entries(reward.components).map(([key, val]: [string, any]) => (
                    <div key={key} className="flex justify-between text-[10px]">
                      <span className="text-slate-500 capitalize">{key.replace('_', ' ')}</span>
                      <span className={val >= 0 ? 'text-emerald-500' : 'text-rose-500'}>{val >= 0 ? '+' : ''}{val}</span>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}

            {done && (
              <div className="space-y-3">
                {!score && (
                  <button 
                    onClick={grade}
                    className="w-full bg-emerald-600 hover:bg-emerald-500 text-white font-bold py-3 rounded-lg transition-all flex items-center justify-center gap-2 shadow-lg shadow-emerald-900/20"
                  >
                    <CheckCircle2 size={20} /> Calculate Final Grade
                  </button>
                )}
                {score !== null && (
                  <motion.div 
                    initial={{ scale: 0.9, opacity: 0 }}
                    animate={{ scale: 1, opacity: 1 }}
                    className="text-center p-6 bg-emerald-500/10 border border-emerald-500/30 rounded-xl"
                  >
                    <div className="text-xs text-emerald-500 uppercase font-bold tracking-widest mb-2">Final Score</div>
                    <div className="text-5xl font-black text-white">{(score * 100).toFixed(1)}%</div>
                    <div className="mt-4 text-xs text-slate-400">
                      Deterministic grade based on priority satisfaction and deadline compliance.
                    </div>
                  </motion.div>
                )}
              </div>
            )}
          </section>
        </div>
      </main>
    </div>
  );
}
