export default function LogsTab({ logs }: { logs: string[] }) {
  return (
    <div className="bg-slate-900 text-green-400 font-mono text-sm p-4 rounded-xl h-[500px] overflow-y-auto">
      {logs.length === 0 ? (
        <div className="text-slate-500">No logs yet.</div>
      ) : (
        logs.map((log, i) => (
          <div key={i} className="mb-1">
            {log}
          </div>
        ))
      )}
    </div>
  );
}