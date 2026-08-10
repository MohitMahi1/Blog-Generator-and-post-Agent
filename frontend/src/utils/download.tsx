import { renderToStaticMarkup } from 'react-dom/server';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import type { DownloadFormat } from '../types/blog';

const slugify = (title: string) =>
  (title || 'blog').replace(/\s+/g, '_').replace(/[^a-zA-Z0-9_-]/g, '').toLowerCase();

function markdownToHtml(markdown: string): string {
  return renderToStaticMarkup(
    <ReactMarkdown remarkPlugins={[remarkGfm]}>{markdown}</ReactMarkdown>
  );
}

/** Plain markdown file download. */
export function downloadMarkdown(markdown: string, title: string): void {
  const blob = new Blob([markdown], { type: 'text/markdown;charset=utf-8' });
  triggerDownload(blob, `${slugify(title)}.md`);
}

/**
 * Word-compatible .doc download. We write the blog as simple HTML inside a
 * .doc container — Microsoft Word opens it natively.
 */
export function downloadWord(markdown: string, title: string): void {
  const html = `<!DOCTYPE html>
<html xmlns:o="urn:schemas-microsoft-com:office:office"
      xmlns:w="urn:schemas-microsoft-com:office:word">
<head>
  <meta charset="utf-8" />
  <title>${title}</title>
  <!--[if gte mso 9]><xml><w:WordDocument><w:View>Print</w:View></w:WordDocument></xml><![endif]-->
  <style>
    body { font-family: Calibri, Arial, sans-serif; font-size: 12pt; line-height: 1.6; color: #1f2937; max-width: 800px; margin: 40px auto; }
    h1 { font-size: 26pt; } h2 { font-size: 20pt; } h3 { font-size: 16pt; }
    img { max-width: 100%; }
    pre { background: #f1f5f9; padding: 12px; border-radius: 6px; }
    code { font-family: Consolas, monospace; }
    a { color: #2563eb; }
  </style>
</head>
<body>${markdownToHtml(markdown)}</body>
</html>`;

  const blob = new Blob(['\ufeff', html], { type: 'application/msword' });
  triggerDownload(blob, `${slugify(title)}.doc`);
}

/**
 * PDF export via the browser's print dialog. Renders a clean styled document
 * in a hidden iframe and triggers Print → "Save as PDF". No external libs.
 */
export function downloadPdf(markdown: string, title: string): void {
  const html = `<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8" />
  <title>${title}</title>
  <style>
    body { font-family: Georgia, 'Times New Roman', serif; font-size: 12pt; line-height: 1.7; color: #111827; max-width: 720px; margin: 40px auto; padding: 0 24px; }
    h1 { font-size: 24pt; margin-bottom: 8px; }
    h2 { font-size: 18pt; margin-top: 28px; border-bottom: 1px solid #e5e7eb; padding-bottom: 6px; }
    h3 { font-size: 14pt; margin-top: 20px; }
    img { max-width: 100%; }
    pre { background: #f3f4f6; padding: 12px; border-radius: 6px; font-size: 10pt; white-space: pre-wrap; }
    code { font-family: Consolas, monospace; }
    a { color: #2563eb; }
    blockquote { border-left: 3px solid #d1d5db; margin-left: 0; padding-left: 16px; color: #4b5563; }
    table { border-collapse: collapse; width: 100%; }
    th, td { border: 1px solid #d1d5db; padding: 6px 10px; }
    @media print { body { margin: 0; } }
  </style>
</head>
<body>
  <h1>${title}</h1>
  ${markdownToHtml(markdown)}
</body>
</html>`;

  const iframe = document.createElement('iframe');
  // Off-screen but with a real size so the print layout isn't collapsed.
  iframe.style.position = 'fixed';
  iframe.style.left = '-9999px';
  iframe.style.top = '0';
  iframe.style.width = '800px';
  iframe.style.height = '600px';
  iframe.style.border = '0';
  iframe.title = 'pdf-print';
  iframe.srcdoc = html;
  document.body.appendChild(iframe);

  iframe.onload = () => {
    try {
      iframe.contentWindow?.focus();
      // Give the browser a beat to lay out the document, then open Print → Save as PDF.
      setTimeout(() => {
        try {
          iframe.contentWindow?.print();
        } catch (err) {
          console.error('PDF print failed:', err);
        }
      }, 250);
    } catch (err) {
      console.error('PDF export failed:', err);
      iframe.remove();
    }
  };

  // Fallback cleanup once printing has had a chance to happen.
  setTimeout(() => iframe.remove(), 60000);
}

function triggerDownload(blob: Blob, filename: string): void {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(url);
}

export function downloadByFormat(format: DownloadFormat, markdown: string, title: string): void {
  if (format === 'md') downloadMarkdown(markdown, title);
  else if (format === 'word') downloadWord(markdown, title);
  else downloadPdf(markdown, title);
}
