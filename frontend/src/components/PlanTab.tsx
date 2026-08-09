import type { Plan } from '../types/blog';

export default function PlanTab({ plan }: { plan?: Plan | null }) {
  if (!plan) {
    return <div className="text-slate-500">No plan available yet.</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-semibold">{plan.blog_title}</h3>
        <div className="flex gap-6 mt-2 text-sm text-slate-600">
          <span><strong>Audience:</strong> {plan.audience}</span>
          <span><strong>Tone:</strong> {plan.tone}</span>
          <span><strong>Kind:</strong> {plan.blog_kind}</span>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="min-w-full text-sm border border-slate-200 rounded-lg overflow-hidden">
          <thead className="bg-slate-100">
            <tr>
              <th className="px-4 py-2 text-left">ID</th>
              <th className="px-4 py-2 text-left">Title</th>
              <th className="px-4 py-2 text-left">Words</th>
              <th className="px-4 py-2 text-left">Research</th>
              <th className="px-4 py-2 text-left">Citations</th>
              <th className="px-4 py-2 text-left">Code</th>
            </tr>
          </thead>
          <tbody>
            {plan.tasks.map((t) => (
              <tr key={t.id} className="border-t border-slate-200">
                <td className="px-4 py-2">{t.id}</td>
                <td className="px-4 py-2">{t.title}</td>
                <td className="px-4 py-2">{t.target_words}</td>
                <td className="px-4 py-2">{t.requires_research ? 'Yes' : 'No'}</td>
                <td className="px-4 py-2">{t.requires_citations ? 'Yes' : 'No'}</td>
                <td className="px-4 py-2">{t.requires_code ? 'Yes' : 'No'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}