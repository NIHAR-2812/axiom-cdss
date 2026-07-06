import { useState, useEffect } from 'react';
import { Activity, CheckCircle, ShieldAlert, X } from 'lucide-react';
import { login, getDiagnosis } from './services/api';

function App() {
  // --- STATE MANAGEMENT ---
  const [symptoms, setSymptoms] = useState([]); // Dynamic symptom array
  const [inputValue, setInputValue] = useState(""); // Current text in the search bar
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // --- LIFECYCLE ---
  // Auto-login the test doctor on load
  useEffect(() => {
    login("dr_smith", "secure_password_123")
      .then(() => console.log("Authenticated successfully."))
      .catch(err => setError("Authentication failed. Is FastAPI running?"));
  }, []);

  // --- HANDLERS ---
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && inputValue.trim() !== '') {
      const newSymptom = inputValue.trim().toLowerCase();
      // Prevent duplicates
      if (!symptoms.includes(newSymptom)) {
        setSymptoms([...symptoms, newSymptom]);
      }
      setInputValue(""); // Clear the input bar
    }
  };

  const removeSymptom = (symptomToRemove) => {
    setSymptoms(symptoms.filter(s => s !== symptomToRemove));
  };

  const handleAnalyze = async () => {
    if (symptoms.length === 0) {
      setError("Please enter at least one symptom before analyzing.");
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const data = await getDiagnosis(symptoms);
      setResults(data);
    } catch (err) {
      console.error(err);
      setError("Inference failed. Please check if the symptoms are recognized by the model.");
    }
    setLoading(false);
  };

  return (
    <div className="max-w-6xl mx-auto p-8">
      
      {/* Header */}
      <header className="flex items-center justify-between mb-10">
        <div>
          <h1 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-blue-400 to-emerald-400">
            Neural Nexus CDSS
          </h1>
          <p className="text-gray-400 mt-2">Clinical Decision Support Engine</p>
        </div>
        <button 
          onClick={handleAnalyze}
          disabled={loading || symptoms.length === 0}
          className="bg-blue-600 hover:bg-blue-500 disabled:bg-blue-800 disabled:opacity-50 px-8 py-3 rounded-xl font-semibold transition-all shadow-[0_0_15px_rgba(37,99,235,0.5)] flex items-center gap-2"
        >
          <Activity size={20} className={loading ? "animate-spin" : ""} />
          {loading ? "Processing..." : "Run Inference"}
        </button>
      </header>

      {/* Error Banner */}
      {error && (
        <div className="bg-red-500/20 border border-red-500/50 text-red-200 p-4 rounded-xl mb-8 flex items-center gap-3 animate-in fade-in duration-300">
          <ShieldAlert size={20} />
          {error}
        </div>
      )}

      {/* Symptom Input Panel */}
      <div className="glass-panel rounded-2xl p-6 mb-8">
        <h2 className="text-gray-300 font-medium mb-4">Patient Symptoms</h2>
        
        {/* Render the selected tags */}
        <div className="flex flex-wrap gap-2 mb-4">
          {symptoms.map((symptom, idx) => (
            <span 
              key={idx} 
              className="bg-blue-500/20 text-blue-300 border border-blue-500/30 px-3 py-1 rounded-full flex items-center gap-2 text-sm backdrop-blur-sm transition-all hover:bg-blue-500/30"
            >
              {symptom}
              <button 
                onClick={() => removeSymptom(symptom)}
                className="hover:text-red-400 transition-colors focus:outline-none flex items-center justify-center"
                aria-label={`Remove ${symptom}`}
              >
                <X size={14} strokeWidth={3} />
              </button>
            </span>
          ))}
          {symptoms.length === 0 && (
            <span className="text-gray-500 text-sm italic py-1">No symptoms added yet. Type below and press Enter.</span>
          )}
        </div>

        {/* The Input Bar */}
        <input 
          type="text"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="Type a symptom (e.g., 'coughing') and press Enter..."
          className="w-full bg-slate-900/50 border border-slate-700/50 rounded-xl px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all shadow-inner"
        />
      </div>

      {/* Bento Grid layout - Only shows when we have results */}
      {results && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
          
          {/* Tile 1: Primary Diagnosis (Spans 1 col) */}
          <div className="md:col-span-1 glass-panel rounded-3xl p-8 flex flex-col justify-center items-center text-center">
            <h2 className="text-gray-400 font-medium uppercase tracking-wider text-sm mb-4">AI Prediction</h2>
            <div className="text-6xl font-black text-white drop-shadow-md">
              {results.ai_predicted_icd10}
            </div>
            
            {/* Dynamic Confidence indicator */}
            <div className={`mt-6 px-4 py-2 rounded-full text-sm font-bold flex items-center gap-2 shadow-inner ${
              results.confidence_score > 0.7 ? 'bg-emerald-500/20 text-emerald-400 border border-emerald-500/30' : 'bg-orange-500/20 text-orange-400 border border-orange-500/30'
            }`}>
              Confidence: {(results.confidence_score * 100).toFixed(1)}%
            </div>
          </div>

          {/* Tile 2: Graph Validated Treatments (Spans 2 cols) */}
          <div className="md:col-span-2 glass-panel rounded-3xl p-8">
            <div className="flex items-center justify-between border-b border-white/10 pb-4 mb-4">
              <h2 className="text-xl font-semibold text-gray-200">Treatment Pathway</h2>
              {results.integrity_check && (
                <span className="flex items-center gap-2 text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1 rounded-full text-sm font-medium shadow-sm">
                  <CheckCircle size={16} /> Graph Verified
                </span>
              )}
            </div>
            
            {results.graph_validated_medications.length > 0 ? (
              <div className="flex flex-wrap gap-3 mt-6">
                {results.graph_validated_medications.map((med, idx) => (
                  <div key={idx} className="bg-slate-800/50 border border-slate-700/50 px-6 py-3 rounded-xl shadow-inner text-lg font-medium text-slate-200">
                    {med}
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-gray-500 italic mt-4">No verified treatments found in Knowledge Graph.</p>
            )}
          </div>

          {/* Tile 3: Explainable AI Breakdown (Spans all 3 cols) */}
          <div className="md:col-span-3 glass-panel rounded-3xl p-8">
            <h2 className="text-xl font-semibold text-gray-200 mb-6">Explainability (XAI) Weights</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              {Object.entries(results.xai_analysis).map(([symptom, weight]) => (
                <div key={symptom}>
                  <div className="flex justify-between text-sm mb-3 text-gray-300 font-medium">
                    <span className="capitalize">{symptom}</span>
                    <span className="text-blue-300">{(weight * 100).toFixed(1)}%</span>
                  </div>
                  {/* Progress Bar Container */}
                  <div className="w-full bg-slate-800/80 rounded-full h-3 shadow-inner overflow-hidden border border-slate-700/50">
                    <div 
                      className="bg-gradient-to-r from-blue-500 to-cyan-400 h-full rounded-full transition-all duration-1000 ease-out shadow-[0_0_10px_rgba(56,189,248,0.5)]" 
                      style={{ width: `${weight * 100}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>
      )}
    </div>
  );
}

export default App;