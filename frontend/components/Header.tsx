import { useState } from 'react';
import { BookOpen, Settings } from 'lucide-react';

const DEFAULT_VENUES = [
  { key: 'NeurIPS', label: 'NeurIPS' },
  { key: 'ICML', label: 'ICML' },
  { key: 'ICLR', label: 'ICLR' },
  { key: 'AAAI', label: 'AAAI' },
  { key: 'CVPR', label: 'CVPR' },
  { key: 'ICCV', label: 'ICCV' },
  { key: 'ACL', label: 'ACL' },
  { key: 'EMNLP', label: 'EMNLP' },
  { key: 'OSDI', label: 'OSDI' },
  { key: 'SOSP', label: 'SOSP' },
  { key: 'NSDI', label: 'NSDI' },
  { key: 'SIGCOMM', label: 'SIGCOMM' },
];

export interface ResearchSettings {
  venues: string[];
  maxPapers: number;
  yearStart: number;
  yearEnd: number;
}

interface HeaderProps {
  settings: ResearchSettings;
  onSettingsChange: (s: ResearchSettings) => void;
}

export default function Header({ settings, onSettingsChange }: HeaderProps) {
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState<ResearchSettings>(settings);

  const toggleVenue = (key: string) => {
    setDraft(prev => ({
      ...prev,
      venues: prev.venues.includes(key)
        ? prev.venues.filter(v => v !== key)
        : [...prev.venues, key],
    }));
  };

  const save = () => {
    onSettingsChange(draft);
    setOpen(false);
  };

  return (
    <header className="bg-white border-b border-gray-200 sticky top-0 z-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <div className="flex items-center space-x-3">
            <div className="flex items-center justify-center w-10 h-10 bg-primary-600 rounded-lg">
              <BookOpen className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">Research Agent</h1>
              <p className="text-xs text-gray-500">智能研究助手</p>
            </div>
          </div>

          <div className="relative">
            <button
              onClick={() => { setDraft(settings); setOpen(!open); }}
              className="flex items-center space-x-2 px-4 py-2 text-gray-600 hover:text-primary-600 transition-colors"
            >
              <Settings className="w-4 h-4" />
              <span className="text-sm">设置</span>
            </button>

            {open && (
              <>
                <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
                <div className="absolute right-0 top-12 z-50 w-80 bg-white rounded-xl shadow-lg border border-gray-200 p-5">
                  <h3 className="font-semibold text-gray-900 mb-1">研究设置</h3>

                  <div className="mt-3">
                    <label className="text-sm text-gray-600">搜索论文数</label>
                    <input
                      type="number" min={1} max={20}
                      value={draft.maxPapers}
                      onChange={e => setDraft(p => ({ ...p, maxPapers: +e.target.value }))}
                      className="mt-1 w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none"
                    />
                  </div>

                  <div className="mt-3">
                    <label className="text-sm text-gray-600">年份范围</label>
                    <div className="flex items-center gap-2 mt-1">
                      <input type="number" min={2010} max={2026} value={draft.yearStart}
                        onChange={e => setDraft(p => ({ ...p, yearStart: +e.target.value }))}
                        className="w-20 px-2 py-1.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none" />
                      <span className="text-gray-400">—</span>
                      <input type="number" min={2010} max={2026} value={draft.yearEnd}
                        onChange={e => setDraft(p => ({ ...p, yearEnd: +e.target.value }))}
                        className="w-20 px-2 py-1.5 border border-gray-200 rounded-lg text-sm focus:ring-2 focus:ring-primary-500 outline-none" />
                    </div>
                  </div>

                  <div className="mt-3">
                    <label className="text-sm text-gray-600">搜索范围（顶会/顶刊）</label>
                    <div className="mt-1 grid grid-cols-2 gap-1 max-h-48 overflow-y-auto">
                      {DEFAULT_VENUES.map(v => (
                        <label key={v.key} className="flex items-center gap-1.5 text-sm cursor-pointer hover:bg-gray-50 rounded px-1 py-0.5">
                          <input
                            type="checkbox"
                            checked={draft.venues.includes(v.key)}
                            onChange={() => toggleVenue(v.key)}
                            className="rounded text-primary-600"
                          />
                          {v.label}
                        </label>
                      ))}
                    </div>
                  </div>

                  <div className="flex gap-2 mt-4">
                    <button onClick={save} className="flex-1 px-4 py-2 bg-primary-600 text-white text-sm rounded-lg hover:bg-primary-700 transition-colors">
                      保存
                    </button>
                    <button onClick={() => setOpen(false)} className="px-4 py-2 text-sm text-gray-500 hover:bg-gray-100 rounded-lg transition-colors">
                      取消
                    </button>
                  </div>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}
