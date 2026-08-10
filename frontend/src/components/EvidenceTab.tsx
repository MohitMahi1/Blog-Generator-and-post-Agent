import type { EvidenceItem } from '../types/blog';

interface Props {
  evidence?: EvidenceItem[];
  queries?: string[];
}

export default function EvidenceTab({ evidence = [], queries = [] }: Props) {
  if (evidence.length === 0 && queries.length === 0) {
    return <div className="text-slate-500">No research evidence returned (closed_book mode or no results).</div>;
  }

  return (
    <div className="space-y-6">
      {/* Generated Search Queries */}
      {queries.length > 0 && (
        <div className="bg-slate-50 p-4 rounded-xl border border-slate-200">
          <h3 className="text-sm font-semibold text-slate-700 mb-2 flex items-center gap-2">
            <span>🔍 Generated Tavily Search Queries ({queries.length}):</span>
          </h3>
          <div className="flex flex-wrap gap-2">
            {queries.map((q, idx) => (
              <span
                key={idx}
                className="bg-white text-slate-700 px-3 py-1.5 rounded-lg border border-slate-300 text-xs font-mono shadow-sm"
              >
                "{q}"
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Evidence Sources Table */}
      {evidence.length > 0 ? (
        <div>
          <h3 className="text-sm font-semibold text-slate-700 mb-3 flex items-center gap-2">
            <span>📚 Research Sources Found ({evidence.length}):</span>
          </h3>
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm border border-slate-200 rounded-lg overflow-hidden">
              <thead className="bg-slate-100 text-slate-700 font-medium">
                <tr>
                  <th className="px-4 py-2.5 text-left">Title</th>
                  <th className="px-4 py-2.5 text-left">Snippet</th>
                  <th className="px-4 py-2.5 text-left">Published</th>
                  <th className="px-4 py-2.5 text-left">Source</th>
                  <th className="px-4 py-2.5 text-left">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 bg-white">
                {evidence.map((e, i) => (
                  <tr key={i} className="hover:bg-slate-50 transition">
                    <td className="px-4 py-3 font-medium text-slate-800 max-w-xs truncate" title={e.title}>
                      {e.title || 'Untitled Source'}
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-500 max-w-md truncate" title={e.snippet || ''}>
                      {e.snippet || '—'}
                    </td>
                    <td className="px-4 py-3 text-xs text-slate-600 whitespace-nowrap">{e.published_at || '—'}</td>
                    <td className="px-4 py-3 text-xs text-slate-600 whitespace-nowrap">{e.source || '—'}</td>
                    <td className="px-4 py-3 whitespace-nowrap">
                      <a
                        href={e.url}
                        target="_blank"
                        rel="noreferrer"
                        className="inline-flex items-center gap-1 text-xs bg-blue-50 text-blue-600 hover:bg-blue-100 font-medium px-2.5 py-1 rounded-md transition"
                      >
                        🔗 Open
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="text-xs text-slate-500">No web evidence sources matched filtering criteria.</div>
      )}
    </div>
  );
}