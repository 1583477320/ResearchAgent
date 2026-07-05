import { useState, useEffect } from 'react';
import { Clock, Trash2, RefreshCw, Plus } from 'lucide-react';

interface Session {
  id: string;
  topic: string;
  status: string;
  started_at: string;
  paper_count: number;
}

interface Props {
  onSelect: (sessionId: string) => void;
  onNew: () => void;
  refreshTrigger: number;
  activeId?: string;
}

export default function ResearchHistory({ onSelect, onNew, refreshTrigger, activeId }: Props) {
  const [sessions, setSessions] = useState<Session[]>([]);

  const fetchHistory = async () => {
    try {
      const res = await fetch('/api/history?limit=20');
      const data = await res.json();
      setSessions(data.sessions || []);
    } catch (e) { console.error('History fetch failed:', e); }
  };

  useEffect(() => { fetchHistory(); }, [refreshTrigger]);

  const handleDelete = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm('删除这条研究记录？')) return;
    await fetch(`/api/history/${id}`, { method: 'DELETE' });
    fetchHistory();
  };

  const formatTime = (ts: string) => {
    const d = new Date(ts);
    return `${d.getMonth() + 1}/${d.getDate()} ${String(d.getHours()).padStart(2, '0')}:${String(d.getMinutes()).padStart(2, '0')}`;
  };

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
        <div className="flex items-center gap-2 text-gray-700 font-semibold text-sm">
          <Clock className="w-4 h-4" /> 研究历史
        </div>
        <div className="flex gap-1">
          <button onClick={onNew} title="新建研究"
            className="flex items-center gap-1 px-2 py-1 text-xs text-primary-600 hover:bg-primary-50 rounded transition-colors">
            <Plus className="w-3.5 h-3.5" /> 新建
          </button>
          <button onClick={fetchHistory} title="刷新"
            className="p-1 hover:bg-gray-100 rounded transition-colors">
            <RefreshCw className="w-3.5 h-3.5 text-gray-400" />
          </button>
        </div>
      </div>

      {sessions.length === 0 ? (
        <div className="px-4 py-6 text-center text-gray-400 text-sm">暂无研究记录</div>
      ) : (
        <div className="divide-y divide-gray-50 max-h-[calc(100vh-280px)] overflow-y-auto">
          {sessions.map((s) => (
            <div key={s.id} onClick={() => onSelect(s.id)}
              className={`flex items-center justify-between px-4 py-2.5 cursor-pointer transition-colors group
                ${s.id === activeId ? 'bg-primary-50 border-l-2 border-primary-500' : 'hover:bg-gray-50'}`}>
              <div className="min-w-0 flex-1">
                <div className="text-sm text-gray-800 truncate">{s.topic}</div>
                <div className="flex items-center gap-2 mt-0.5">
                  <span className={`text-xs px-1.5 py-0.5 rounded ${
                    s.status === 'completed' ? 'bg-green-100 text-green-700' :
                    s.status === 'failed' ? 'bg-red-100 text-red-700' :
                    'bg-blue-100 text-blue-700'}`}>
                    {s.status === 'completed' ? '完成' : s.status === 'failed' ? '失败' : '运行中'}
                  </span>
                  <span className="text-xs text-gray-400">{formatTime(s.started_at)}</span>
                  {s.paper_count > 0 && <span className="text-xs text-gray-400">{s.paper_count}篇</span>}
                </div>
              </div>
              <button onClick={(e) => handleDelete(s.id, e)}
                className="ml-2 p-1 text-gray-300 hover:text-red-500 opacity-0 group-hover:opacity-100 transition-all">
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
