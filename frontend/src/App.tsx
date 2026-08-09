import { useState } from "react";
import Sidebar from "./components/Sidebar";
import PlanTab from "./components/PlanTab";
import EvidenceTab from "./components/EvidenceTab";
import PreviewTab from "./components/PreviewTab";
import ImagesTab from "./components/ImagesTab";
import LogsTab from "./components/LogsTab";
import { generateBlog } from "./api/blog";
import type {
  GenerateResponse,
  Plan,
  EvidenceItem,
  ImageSpec,
} from "./types/blog";

type Tab = "plan" | "evidence" | "preview" | "images" | "logs";

export default function App() {
  const [topic, setTopic] = useState("");
  const [asOf, setAsOf] = useState(new Date().toISOString().slice(0, 10));
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<Tab>("plan");
  const [logs, setLogs] = useState<string[]>([]);
  const [result, setResult] = useState<GenerateResponse | null>(null);

  // We keep extra fields that the current simple API does not return yet
  const [plan, setPlan] = useState<Plan | null>(null);
  const [evidence, setEvidence] = useState<EvidenceItem[]>([]);
  const [imageSpecs, setImageSpecs] = useState<ImageSpec[]>([]);

  const addLog = (msg: string) => {
    setLogs((prev) => [...prev, `[${new Date().toLocaleTimeString()}] ${msg}`]);
  };

  const handleGenerate = async () => {
    if (!topic.trim()) return;

    setLoading(true);
    setLogs([]);
    setResult(null);
    setPlan(null);
    setEvidence([]);
    setImageSpecs([]);
    setActiveTab("logs");

    addLog("Starting generation…");

    try {
      const data = await generateBlog(topic, asOf);
      setResult(data);

      // NEW: populate the extra states
      setPlan(data.plan || null);
      setEvidence(data.evidence || []);
      setImageSpecs(data.image_specs || []);
      setLogs(data.logs || []);

      addLog(`✅ Done — Mode: ${data.mode}, Sections: ${data.sections_count}`);
      setActiveTab("preview");
    } catch (err: any) {
      console.error(err);
      addLog(`❌ Error: ${err?.response?.data?.detail || err.message}`);
    } finally {
      setLoading(false);
    }
  };

  const tabs: { id: Tab; label: string }[] = [
    { id: "plan", label: "🧩 Plan" },
    { id: "evidence", label: "🔎 Evidence" },
    { id: "preview", label: "📝 Markdown Preview" },
    { id: "images", label: "🖼️ Images" },
    { id: "logs", label: "🧾 Logs" },
  ];

  return (
    <div className="flex min-h-screen">
      <Sidebar
        topic={topic}
        setTopic={setTopic}
        asOf={asOf}
        setAsOf={setAsOf}
        onGenerate={handleGenerate}
        loading={loading}
      />

      <main className="flex-1 p-6">
        {/* Tabs */}
        <div className="flex gap-2 border-b border-slate-200 mb-6">
          {tabs.map((t) => (
            <button
              key={t.id}
              onClick={() => setActiveTab(t.id)}
              className={`px-4 py-2 text-sm font-medium rounded-t-lg transition ${
                activeTab === t.id
                  ? "bg-white border border-b-0 border-slate-200 text-blue-600"
                  : "text-slate-600 hover:text-slate-900"
              }`}
            >
              {t.label}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="bg-white rounded-xl border border-slate-200 p-6 min-h-[600px]">
          {activeTab === "plan" && <PlanTab plan={plan} />}
          {activeTab === "evidence" && <EvidenceTab evidence={evidence} />}
          {activeTab === "preview" && (
            <PreviewTab
              markdown={result?.final_markdown || ""}
              title={result?.blog_title || "blog"}
            />
          )}
          {activeTab === "images" && <ImagesTab specs={imageSpecs} />}
          {activeTab === "logs" && <LogsTab logs={logs} />}
        </div>
      </main>
    </div>
  );
}
