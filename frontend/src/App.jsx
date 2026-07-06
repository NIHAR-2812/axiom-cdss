import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Plus, X, Brain, Activity, CheckCircle2, ShieldAlert, ShieldCheck, Clock, Network } from 'lucide-react';

function App() {
  // --- STATE MANAGEMENT ---
  const [token, setToken] = useState(null);
  const [symptomInput, setSymptomInput] = useState('');
  const [symptoms, setSymptoms] = useState([]);
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [auditLogs, setAuditLogs] = useState([]);
  
  const fetchLogs = async () => {
    if (!token) return;
    try {
      const response = await axios.get('http://127.0.0.1:8000/api/v1/audit/logs', {
        headers: { 'Authorization': `Bearer ${token}` }
      });
      setAuditLogs(response.data);
    } catch (err) {
      console.error("Failed to fetch logs:", err);
    }
  };

  // Automatically fetch logs when the token is acquired
  useEffect(() => {
    if (token) fetchLogs();
  }, [token]);

  // --- 1. SILENT AUTHENTICATION ---
  // When the app loads, automatically log in to get our JWT
  useEffect(() => {
    const fetchToken = async () => {
      try {
        const formData = new URLSearchParams();
        formData.append('username', 'dr_smith');
        formData.append('password', 'secure_password_123');

        const response = await axios.post('http://127.0.0.1:8000/token', formData, {
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
        });
        setToken(response.data.access_token);
      } catch (err) {
        console.error("Auth failed:", err);
        setError("Failed to connect to authentication server.");
      }
    };
    fetchToken();
  }, []);

  // --- 2. UI LOGIC ---
  const handleAddSymptom = (e) => {
    e.preventDefault();
    if (symptomInput.trim() && !symptoms.includes(symptomInput.trim())) {
      setSymptoms([...symptoms, symptomInput.trim()]);
      setSymptomInput('');
    }
  };

  const removeSymptom = (symptomToRemove) => {
    setSymptoms(symptoms.filter(s => s !== symptomToRemove));
  };

  // --- 3. THE INFERENCE PIPELINE ---
  const runInference = async () => {
    if (symptoms.length === 0) {
      setError("Please add at least one symptom.");
      return;
    }
    
    setLoading(true);
    setError(null);

    try {
      const response = await axios.post(
        'http://127.0.0.1:8000/api/v1/inference/predict',
        { symptoms: symptoms },
        {
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${token}`
          }
        }
      );
      setResults(response.data);
      fetchLogs();
    } catch (err) {
      console.error(err);
      setError(err.response?.data?.detail || "Failed to reach AI engine.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen p-4 md:p-8 flex flex-col gap-6 font-sans">
      
      {/* HEADER */}
      <header className="glass-panel p-6 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <Activity className="text-cdss-primary w-8 h-8" />
          <div>
            <h1 className="text-2xl font-bold text-white tracking-wide">Axiom CDSS</h1>
            <p className="text-xs text-slate-400 mt-1">Clinical Decision Support System</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className={`h-2 w-2 rounded-full ${token ? 'bg-emerald-500 animate-pulse' : 'bg-red-500'}`}></div>
          <span className="text-sm text-slate-300 font-medium">
            {token ? 'Dr. Smith (Secured)' : 'Connecting...'}
          </span>
        </div>
      </header>

      <main className="grid grid-cols-1 lg:grid-cols-12 gap-6 flex-1">
        
        {/* LEFT COLUMN: INPUT */}
        <section className="glass-panel p-6 lg:col-span-4 flex flex-col gap-6">
          <div>
            <h2 className="text-xl font-semibold text-white mb-2 flex items-center gap-2">
              <Brain className="w-5 h-5 text-cdss-accent" />
              Patient Intake
            </h2>
            <p className="text-sm text-slate-400">Enter clinical observations to generate AI predictions.</p>
          </div>
          
          <div className="flex-1 flex flex-col gap-4">
            <form onSubmit={handleAddSymptom} className="flex gap-2">
              <input 
                type="text" 
                value={symptomInput}
                onChange={(e) => setSymptomInput(e.target.value)}
                placeholder="e.g. Increased thirst..."
                className="flex-1 bg-slate-900/50 border border-slate-700 rounded-xl px-4 py-2 text-white focus:outline-none focus:border-cdss-primary transition-colors"
              />
              <button 
                type="submit"
                className="bg-slate-800 hover:bg-slate-700 text-white p-2 rounded-xl border border-slate-700 transition-colors"
              >
                <Plus className="w-5 h-5" />
              </button>
            </form>

            {/* Symptom Chips */}
            <div className="flex flex-wrap gap-2 mt-2">
              {symptoms.map((sym, idx) => (
                <div key={idx} className="bg-cdss-primary/10 border border-cdss-primary/30 text-cdss-primary px-3 py-1.5 rounded-lg text-sm flex items-center gap-2">
                  {sym}
                  <button onClick={() => removeSymptom(sym)} className="hover:text-white transition-colors">
                    <X className="w-4 h-4" />
                  </button>
                </div>
              ))}
              {symptoms.length === 0 && (
                <span className="text-slate-500 text-sm italic">No symptoms added yet.</span>
              )}
            </div>

            {error && (
              <div className="bg-red-500/10 border border-red-500/50 text-red-400 p-3 rounded-xl text-sm flex items-center gap-2">
                <ShieldAlert className="w-4 h-4 shrink-0" />
                {error}
              </div>
            )}
          </div>
          
          <button 
            onClick={runInference}
            disabled={loading || !token}
            className="w-full bg-cdss-primary disabled:bg-slate-700 disabled:text-slate-500 text-slate-900 font-bold py-3 px-4 rounded-xl hover:bg-sky-400 transition-all shadow-lg shadow-sky-500/20 active:scale-95 flex justify-center items-center gap-2"
          >
            {loading ? <span className="animate-pulse">Processing...</span> : 'Run AI Inference'}
          </button>
        </section>

        {/* RIGHT COLUMN: OUTPUT */}
        <section className="glass-panel p-6 lg:col-span-8 flex flex-col gap-6">
          <div className="flex justify-between items-end">
            <h2 className="text-xl font-semibold text-white">Diagnostic Insights</h2>
            {results && results.integrity_check && (
              <span className="text-xs bg-emerald-500/10 text-emerald-400 px-3 py-1 rounded-full border border-emerald-500/30 flex items-center gap-1">
                <CheckCircle2 className="w-3 h-3" /> Graph Validated
              </span>
            )}
          </div>

          {/* Bento Grid Container */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            
            {/* 1. ICD-10 Card */}
            <div className="bg-slate-800/40 p-5 rounded-2xl border border-slate-700/50 flex flex-col justify-center">
              <h3 className="text-sm font-medium text-slate-400 mb-2">Predicted ICD-10</h3>
              <div className="text-4xl font-bold text-cdss-accent">
                {results ? results.ai_predicted_icd10 : '--'}
              </div>
            </div>

            {/* 2. Confidence Card */}
            <div className="bg-slate-800/40 p-5 rounded-2xl border border-slate-700/50 flex flex-col justify-center">
              <h3 className="text-sm font-medium text-slate-400 mb-2">AI Confidence</h3>
              <div className={`text-4xl font-bold ${results && results.confidence_score > 0.85 ? 'text-emerald-400' : 'text-amber-400'}`}>
                {results ? `${(results.confidence_score * 100).toFixed(1)}%` : '--%'}
              </div>
            </div>
            
            {/* 3. Treatments Card (Full Width) */}
            <div className="bg-slate-800/40 p-5 rounded-2xl border border-slate-700/50 md:col-span-2 min-h-[150px]">
              <h3 className="text-sm font-medium text-slate-400 mb-2">Graph-Validated Treatments</h3>
              <div className="flex gap-2 flex-wrap mt-4">
                {!results ? (
                  <span className="px-3 py-1 rounded-lg bg-slate-700/50 text-slate-500 text-sm border border-slate-600/50">Awaiting inference...</span>
                ) : (
                  results.graph_validated_medications.map((med, idx) => (
                    <span key={idx} className="px-3 py-1 rounded-lg bg-emerald-500/10 text-emerald-300 text-sm border border-emerald-500/30 font-medium">
                      {med}
                    </span>
                  ))
                )}
              </div>
            </div>

            {/* 4. NEW: Explainable AI (XAI) Feature Importance Card (Full Width) */}
            <div className="bg-slate-800/40 p-5 rounded-2xl border border-slate-700/50 md:col-span-2">
              <h3 className="text-sm font-medium text-slate-400 mb-4 flex items-center gap-2">
                <Network className="w-4 h-4 text-cdss-accent" />
                AI Reasoning (Feature Attribution)
              </h3>
              
              {!results || !results.xai_analysis ? (
                <div className="text-slate-500 text-sm italic">Awaiting inference data to generate explanation...</div>
              ) : (
                <div className="flex flex-col gap-3">
                  {Object.entries(results.xai_analysis)
                    .sort(([, a], [, b]) => b - a) // Sort highest weight to lowest
                    .map(([symptom, weight]) => (
                    <div key={symptom} className="flex flex-col gap-1">
                      <div className="flex justify-between text-xs">
                        <span className="text-slate-300">{symptom}</span>
                        <span className="text-cdss-primary font-mono">{(weight * 100).toFixed(1)}%</span>
                      </div>
                      <div className="w-full bg-slate-900 rounded-full h-1.5 overflow-hidden">
                        <div 
                          className="bg-cdss-primary h-1.5 rounded-full transition-all duration-1000 ease-out"
                          style={{ width: `${weight * 100}%` }}
                        ></div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

          </div>
        </section>
        
        {/* BOTTOM ROW: AUDIT LOGS */}
        <section className="glass-panel p-6 lg:col-span-12 flex flex-col gap-4 mt-2">
          <div className="flex justify-between items-center border-b border-slate-700/50 pb-4">
            <h2 className="text-lg font-semibold text-white flex items-center gap-2">
              <ShieldCheck className="w-5 h-5 text-emerald-400" />
              HIPAA Audit Trail
            </h2>
            <button onClick={fetchLogs} className="text-xs text-slate-400 hover:text-white flex items-center gap-1 transition-colors">
              <Clock className="w-3 h-3" /> Refresh Logs
            </button>
          </div>
          
          <div className="overflow-x-auto">
            <table className="w-full text-sm text-left">
              <thead className="text-xs text-slate-400 uppercase bg-slate-900/30">
                <tr>
                  <th className="px-4 py-3 rounded-tl-lg">Timestamp</th>
                  <th className="px-4 py-3">Physician</th>
                  <th className="px-4 py-3">Symptoms Input</th>
                  <th className="px-4 py-3">AI Prediction</th>
                  <th className="px-4 py-3 rounded-tr-lg">Graph Verified</th>
                </tr>
              </thead>
              <tbody>
                {auditLogs.length === 0 ? (
                  <tr>
                    <td colSpan="5" className="px-4 py-8 text-center text-slate-500 italic">No inference logs found for this session.</td>
                  </tr>
                ) : (
                  auditLogs.map((log) => (
                    <tr key={log.id} className="border-b border-slate-800 hover:bg-slate-800/30 transition-colors">
                      <td className="px-4 py-3 text-slate-300 font-mono text-xs">{log.timestamp}</td>
                      <td className="px-4 py-3 text-cdss-primary font-medium">{log.doctor}</td>
                      <td className="px-4 py-3 text-slate-400">{log.symptoms.join(", ")}</td>
                      <td className="px-4 py-3 font-semibold text-cdss-accent">{log.icd10}</td>
                      <td className="px-4 py-3">
                        <span className={`px-2 py-1 rounded text-xs ${log.verified === 'True' ? 'bg-emerald-500/10 text-emerald-400' : 'bg-red-500/10 text-red-400'}`}>
                          {log.verified === 'True' ? 'Verified' : 'Flagged'}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </section>
      </main>
    </div>
  );
}

export default App;