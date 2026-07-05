import { useState, useEffect } from 'react';
import { Upload, FileText, Trash2, FolderOpen, Loader2 } from 'lucide-react';

interface Paper {
  id: string;
  filename: string;
  title: string;
  author: string;
  page_count: number;
  created_at: string;
}

interface FileLibraryProps {
  onPaperSelect?: (paperId: string) => void;
}

export default function FileLibrary({ onPaperSelect }: FileLibraryProps) {
  const [papers, setPapers] = useState<Paper[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [dragOver, setDragOver] = useState(false);
  const [message, setMessage] = useState('');

  useEffect(() => {
    fetchPapers();
  }, []);

  const fetchPapers = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/papers');
      const data = await response.json();
      if (data.success) {
        setPapers(data.papers);
      }
    } catch (error) {
      console.error('Failed to fetch papers:', error);
    }
    setIsLoading(false);
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    await uploadFiles(Array.from(files));
  };

  const handleDrop = async (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(false);
    
    const files = e.dataTransfer.files;
    if (!files || files.length === 0) return;
    
    const pdfFiles = Array.from(files).filter(file => file.type === 'application/pdf');
    if (pdfFiles.length === 0) {
      setMessage('请上传PDF文件');
      setTimeout(() => setMessage(''), 3000);
      return;
    }
    
    await uploadFiles(pdfFiles);
  };

  const handleDragOver = (e: React.DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => {
    setDragOver(false);
  };

  const uploadFiles = async (files: File[]) => {
    setUploading(true);
    setUploadProgress(0);
    setMessage('');

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      
      const formData = new FormData();
      formData.append('file', file);

      try {
        const response = await fetch('/api/upload', {
          method: 'POST',
          body: formData,
        });

        const data = await response.json();
        if (data.success) {
          setMessage(`成功上传: ${file.name}`);
        } else {
          setMessage(`上传失败: ${data.message || '未知错误'}`);
        }
      } catch (error) {
        setMessage(`上传失败: ${file.name}`);
      }

      setUploadProgress(((i + 1) / files.length) * 100);
    }

    await fetchPapers();
    setUploading(false);
    setTimeout(() => setMessage(''), 5000);
  };

  const handleDelete = async (paperId: string) => {
    if (!confirm('确定要删除这篇论文吗？')) return;

    try {
      const response = await fetch(`/api/papers/${paperId}`, {
        method: 'DELETE',
      });

      const data = await response.json();
      if (data.success) {
        setPapers(papers.filter(p => p.id !== paperId));
        setMessage('删除成功');
        setTimeout(() => setMessage(''), 3000);
      }
    } catch (error) {
      console.error('Failed to delete paper:', error);
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    });
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center space-x-2">
          <FolderOpen className="w-5 h-5 text-primary-600" />
          <h3 className="text-lg font-semibold text-gray-900">我的文件库</h3>
        </div>
        <span className="text-sm text-gray-500">{papers.length} 篇论文</span>
      </div>

      <div
        className={`border-2 border-dashed rounded-lg p-8 text-center transition-all cursor-pointer ${
          dragOver 
            ? 'border-primary-500 bg-primary-50' 
            : 'border-gray-300 hover:border-primary-400 hover:bg-gray-50'
        }`}
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => document.getElementById('file-input')?.click()}
      >
        <input
          id="file-input"
          type="file"
          accept=".pdf"
          multiple
          onChange={handleFileChange}
          className="hidden"
        />
        
        <div className="flex flex-col items-center">
          <div className={`w-16 h-16 rounded-full flex items-center justify-center mb-4 ${
            dragOver ? 'bg-primary-100' : 'bg-gray-100'
          }`}>
            <Upload className={`w-8 h-8 ${dragOver ? 'text-primary-600' : 'text-gray-400'}`} />
          </div>
          <p className="text-gray-700 font-medium mb-1">
            {dragOver ? '松开以上传文件' : '拖拽 PDF 文件到这里'}
          </p>
          <p className="text-sm text-gray-500">
            或点击选择文件 · 支持多文件上传 · 最大 50MB
          </p>
        </div>

        {uploading && (
          <div className="mt-4">
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div
                className="bg-primary-600 h-2 rounded-full transition-all"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
            <p className="text-sm text-gray-500 mt-2">上传中...</p>
          </div>
        )}
      </div>

      {message && (
        <div className={`mt-4 p-3 rounded-lg text-sm ${
          message.includes('成功') 
            ? 'bg-green-50 text-green-700' 
            : 'bg-red-50 text-red-700'
        }`}>
          {message}
        </div>
      )}

      <div className="mt-6">
        <h4 className="text-sm font-medium text-gray-700 mb-3">已上传的论文</h4>
        
        {isLoading ? (
          <div className="flex justify-center py-8">
            <Loader2 className="w-6 h-6 text-gray-400 animate-spin" />
          </div>
        ) : papers.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <FileText className="w-12 h-12 mx-auto mb-3 text-gray-300" />
            <p>暂无上传的论文</p>
            <p className="text-sm">拖拽或点击上方区域上传 PDF 文件</p>
          </div>
        ) : (
          <div className="space-y-3">
            {papers.map((paper) => (
              <div
                key={paper.id}
                className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:border-primary-300 hover:bg-gray-50 transition-colors group"
              >
                <div className="flex items-center space-x-4" onClick={() => onPaperSelect?.(paper.id)}>
                  <div className="w-10 h-10 bg-primary-100 rounded-lg flex items-center justify-center">
                    <FileText className="w-5 h-5 text-primary-600" />
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">{paper.title || paper.filename}</p>
                    <p className="text-sm text-gray-500">
                      {paper.author || '未知作者'} · {paper.page_count} 页 · {formatDate(paper.created_at)}
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => handleDelete(paper.id)}
                  className="opacity-0 group-hover:opacity-100 p-2 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-all"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
