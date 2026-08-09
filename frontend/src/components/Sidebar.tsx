interface Props {
  topic: string;
  setTopic: (v: string) => void;
  asOf: string;
  setAsOf: (v: string) => void;
  onGenerate: () => void;
  loading: boolean;
}

export default function Sidebar({ topic, setTopic, asOf, setAsOf, onGenerate, loading }: Props) {
  return (
    <div className="w-80 bg-white border-r border-slate-200 p-5 flex flex-col gap-5 h-screen sticky top-0">
      <h2 className="text-xl font-bold text-slate-800">Blog Writing Agent</h2>

      <div>
        <label className="block text-sm font-medium mb-1">Topic</label>
        <textarea
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          rows={5}
          className="w-full border border-slate-300 rounded-lg p-3 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          placeholder="e.g. Introduction to LangGraph with real examples"
        />
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">As-of date</label>
        <input
          type="date"
          value={asOf}
          onChange={(e) => setAsOf(e.target.value)}
          className="w-full border border-slate-300 rounded-lg p-2 text-sm"
        />
      </div>

      <button
        onClick={onGenerate}
        disabled={loading || !topic.trim()}
        className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-slate-400 text-white font-medium py-2.5 rounded-lg transition"
      >
        {loading ? 'Generating…' : '🚀 Generate Blog'}
      </button>

      <div className="mt-auto text-xs text-slate-400">
        Powered by LangGraph + FastAPI
      </div>
    </div>
  );
}