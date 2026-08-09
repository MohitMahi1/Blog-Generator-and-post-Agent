import type { ImageSpec } from '../types/blog';

export default function ImagesTab({ specs = [] }: { specs?: ImageSpec[] }) {
  if (specs.length === 0) {
    return <div className="text-slate-500">No images generated for this blog.</div>;
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {specs.map((spec) => (
          <div key={spec.filename} className="bg-white border border-slate-200 rounded-xl p-4">
            <img
              src={`http://localhost:8000/images/${spec.filename}`}
              alt={spec.alt}
              className="rounded-lg w-full object-cover"
              onError={(e) => {
                (e.target as HTMLImageElement).style.display = 'none';
              }}
            />
            <p className="mt-2 text-sm font-medium">{spec.caption}</p>
            <p className="text-xs text-slate-500 mt-1">{spec.filename}</p>
          </div>
        ))}
      </div>
    </div>
  );
}