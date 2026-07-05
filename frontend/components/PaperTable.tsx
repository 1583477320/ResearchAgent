import { useState, useRef } from 'react';
import { ExternalLink, FileText, Upload } from 'lucide-react';

interface Paper {
  id: string;
  title: string;
  authors: string[];
  year: string;
  source: string;
  url: string;
  abstract: string;
}

interface PaperTableProps {
  papers: Paper[];
  onPaperAdded?: (paper: Paper) => void;
}

export default function PaperTable({ papers, onPaperAdded }: PaperTableProps) {
  const [uploading, setUploading] = useState(false);
  const fileRef = useRef<HTMLInputElement>(null);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);

      const res = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
      });
      const data = await res.json();
      if (data.success && onPaperAdded) {
        onPaperAdded({
          id: data.paper_id || Date.now().toString(),
          title: file.name.replace(/\.pdf$/i, ''),
          authors: [],
          year: '',
          source: 'Uploaded PDF',
          url: '',
          abstract: `Uploaded: ${data.message || file.name}`,
        });
      }
    } catch (err) {
      console.error('Upload failed:', err);
    }
    setUploading(false);
    if (fileRef.current) fileRef.current.value = '';
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-900">论文列表</h3>
        <div className="flex items-center gap-3">
          <span className="text-sm text-gray-500">{papers.length} 篇论文</span>
          <label className={`flex items-center gap-1 px-3 py-1.5 text-sm text-primary-600 bg-primary-50 rounded-lg cursor-pointer hover:bg-primary-100 transition-colors ${uploading ? 'opacity-50 pointer-events-none' : ''}`}>
            {uploading ? (
              <div className="w-4 h-4 border-2 border-primary-600 border-t-transparent rounded-full animate-spin" />
            ) : (
              <Upload className="w-4 h-4" />
            )}
            {uploading ? '上传中...' : '上传PDF'}
            <input ref={fileRef} type="file" accept="application/pdf" onChange={handleUpload} className="hidden" />
          </label>
        </div>
      </div>

      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            <tr className="border-b border-gray-100">
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">标题</th>
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">作者</th>
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">年份</th>
              <th className="text-left py-3 px-4 text-sm font-medium text-gray-500">来源</th>
              <th className="text-right py-3 px-4 text-sm font-medium text-gray-500">操作</th>
            </tr>
          </thead>
          <tbody>
            {papers.map((paper) => (
              <tr key={paper.id} className="border-b border-gray-50 hover:bg-gray-50 transition-colors">
                <td className="py-3 px-4">
                  <div className="flex items-start space-x-3">
                    <FileText className="w-4 h-4 text-gray-400 mt-0.5 flex-shrink-0" />
                    <div>
                      <a href={paper.url || '#'} target="_blank" rel="noopener noreferrer"
                        className={`text-sm font-medium ${paper.url ? 'text-primary-600 hover:text-primary-700 hover:underline' : 'text-gray-700'}`}>
                        {paper.title}
                      </a>
                      <p className="text-xs text-gray-400 mt-1 line-clamp-2">{paper.abstract}</p>
                    </div>
                  </div>
                </td>
                <td className="py-3 px-4">
                  <span className="text-sm text-gray-600">
                    {paper.authors.length > 0
                      ? `${paper.authors.slice(0, 3).join(', ')}${paper.authors.length > 3 ? ' et al.' : ''}`
                      : '-'}
                  </span>
                </td>
                <td className="py-3 px-4">
                  <span className="text-sm text-gray-600">{paper.year || '-'}</span>
                </td>
                <td className="py-3 px-4">
                  <span className="text-sm text-gray-600">{paper.source}</span>
                </td>
                <td className="py-3 px-4 text-right">
                  {paper.url && (
                    <a href={paper.url} target="_blank" rel="noopener noreferrer"
                      className="inline-flex items-center space-x-1 px-3 py-1.5 text-sm text-primary-600 hover:bg-primary-50 rounded-lg transition-colors">
                      <span>查看</span>
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
