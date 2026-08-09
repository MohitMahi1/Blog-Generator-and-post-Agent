import type { EvidenceItem } from '../types/blog';

export default function EvidenceTab({ evidence = [] }: { evidence?: EvidenceItem[] }) {
  if (evidence.length === 0) {
    return <div className="text-slate-500">No evidence returned (closed_book mode or no results).</div>;
  }

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full text-sm border border-slate-200 rounded-lg overflow-hidden">
        <thead className="bg-slate-100">
          <tr>
            <th className="px-4 py-2 text-left">Title</th>
            <th className="px-4 py-2 text-left">Published</th>
            <th className="px-4 py-2 text-left">Source</th>
            <th className="px-4 py-2 text-left">URL</th>
          </tr>
        </thead>
        <tbody>
          {evidence.map((e, i) => (
            <tr key={i} className="border-t border-slate-200">
              <td className="px-4 py-2">{e.title}</td>
              <td className="px-4 py-2">{e.published_at || '—'}</td>
              <td className="px-4 py-2">{e.source || '—'}</td>
              <td className="px-4 py-2">
                <a href={e.url} target="_blank" rel="noreferrer" className="text-blue-600 hover:underline">
                  Open
                </a>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}