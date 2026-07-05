import { useState } from 'react';
import { Search, Sparkles } from 'lucide-react';

interface SearchInputProps {
  onSearch: (topic: string) => void;
  isLoading: boolean;
  progressMessage?: string;
}

export default function SearchInput({ onSearch, isLoading, progressMessage }: SearchInputProps) {
  const [topic, setTopic] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (topic.trim() && !isLoading) {
      onSearch(topic.trim());
    }
  };

  return (
    <div className="bg-gradient-to-br from-primary-600 to-primary-800 rounded-2xl p-8 mb-8">
      <div className="max-w-3xl mx-auto">
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-12 h-12 bg-white/20 rounded-xl mb-4">
            <Sparkles className="w-6 h-6 text-white" />
          </div>
          <h2 className="text-2xl font-bold text-white mb-2">
            开启您的研究之旅
          </h2>
          <p className="text-primary-100">
            输入研究主题，AI 将为您分析文献、发现研究空白
          </p>
        </div>

        <form onSubmit={handleSubmit} className="relative">
          <div className="relative">
            <input
              type="text"
              value={topic}
              onChange={(e) => setTopic(e.target.value)}
              placeholder="输入您的研究主题，例如：多任务学习、计算机视觉..."
              className="w-full px-6 py-4 pr-32 text-lg rounded-xl border-0 focus:ring-4 focus:ring-white/30 outline-none transition-all"
              disabled={isLoading}
            />
            <button
              type="submit"
              disabled={isLoading || !topic.trim()}
              className="absolute right-2 top-1/2 -translate-y-1/2 flex items-center space-x-2 px-6 py-2.5 bg-white text-primary-600 font-semibold rounded-lg hover:bg-primary-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {isLoading ? (
                <>
                  <div className="w-5 h-5 border-2 border-primary-600 border-t-transparent rounded-full animate-spin" />
                  <span>分析中...</span>
                </>
              ) : (
                <>
                  <Search className="w-5 h-5" />
                  <span>开始研究</span>
                </>
              )}
            </button>
          </div>
        </form>

        {isLoading && progressMessage && (
          <div className="mt-4 bg-white/10 rounded-lg px-4 py-2 text-white text-sm">
            {progressMessage}
          </div>
        )}

        <div className="flex flex-wrap justify-center gap-3 mt-4">
          <span className="text-primary-200 text-sm">热门主题：</span>
          {['多任务学习', '大语言模型', '计算机视觉', '强化学习'].map((tag) => (
            <button
              key={tag}
              onClick={() => !isLoading && setTopic(tag)}
              className="px-3 py-1 bg-white/10 text-white text-sm rounded-full hover:bg-white/20 transition-colors"
            >
              {tag}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
