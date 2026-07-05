import { Lightbulb, Target, MessageSquare, CheckCircle } from 'lucide-react';

interface Gap {
  description: string;
  importance: number;
  feasibility: number;
  potential_value: string;
}

interface ResearchQuestion {
  question: string;
  background: string;
  importance: number;
  assumptions: string[];
}

interface SolvedProblem {
  problem: string;
  solution: string;
  representative_work: string;
}

interface GapAnalysisProps {
  solved_problems: SolvedProblem[];
  research_gaps: Gap[];
  research_questions: ResearchQuestion[];
}

export default function GapAnalysis({ solved_problems, research_gaps, research_questions }: GapAnalysisProps) {
  const renderStarRating = (rating: number) => {
    return Array.from({ length: 5 }).map((_, i) => (
      <span key={i} className={i < rating ? 'text-yellow-400' : 'text-gray-300'}>★</span>
    ));
  };

  return (
    <div className="space-y-6">
      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <div className="flex items-center space-x-2 mb-4">
          <CheckCircle className="w-5 h-5 text-success" />
          <h3 className="text-lg font-semibold text-gray-900">已解决问题</h3>
        </div>
        <div className="space-y-3">
          {solved_problems.length > 0 ? (
            solved_problems.map((item, index) => (
              <div key={index} className="p-4 bg-gray-50 rounded-lg">
                <p className="text-sm font-medium text-gray-900">问题：{item.problem}</p>
                <p className="text-sm text-gray-600 mt-1">解决方案：{item.solution}</p>
                <p className="text-xs text-gray-500 mt-1">代表工作：{item.representative_work}</p>
              </div>
            ))
          ) : (
            <p className="text-sm text-gray-500 italic">暂无数据</p>
          )}
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <div className="flex items-center space-x-2 mb-4">
          <Target className="w-5 h-5 text-warning" />
          <h3 className="text-lg font-semibold text-gray-900">研究空白</h3>
          <span className="text-sm text-gray-500">({research_gaps.length}个)</span>
        </div>
        <div className="space-y-4">
          {research_gaps.length > 0 ? (
            research_gaps.map((gap, index) => (
              <div key={index} className="p-4 border border-gray-200 rounded-lg hover:border-primary-300 transition-colors">
                <div className="flex items-start justify-between mb-2">
                  <span className="text-sm font-medium text-primary-600">空白 {index + 1}</span>
                  <div className="flex items-center space-x-3">
                    <span className="text-xs text-gray-500">
                      重要性 {renderStarRating(gap.importance)}
                    </span>
                    <span className="text-xs text-gray-500">
                      可行性 {renderStarRating(gap.feasibility)}
                    </span>
                  </div>
                </div>
                <p className="text-sm text-gray-700 mb-2">{gap.description}</p>
                <p className="text-xs text-gray-500 bg-gray-50 px-3 py-2 rounded">
                  潜在价值：{gap.potential_value}
                </p>
              </div>
            ))
          ) : (
            <p className="text-sm text-gray-500 italic">暂无数据</p>
          )}
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
        <div className="flex items-center space-x-2 mb-4">
          <MessageSquare className="w-5 h-5 text-info" />
          <h3 className="text-lg font-semibold text-gray-900">研究问题</h3>
          <span className="text-sm text-gray-500">({research_questions.length}个)</span>
        </div>
        <div className="space-y-4">
          {research_questions.length > 0 ? (
            research_questions.map((question, index) => (
              <div key={index} className="p-4 border border-gray-200 rounded-lg hover:border-primary-300 transition-colors">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-primary-600">问题 {index + 1}</span>
                  <span className="text-xs text-gray-500">
                    重要性 {renderStarRating(question.importance)}
                  </span>
                </div>
                <p className="text-sm text-gray-700 font-medium mb-2">{question.question}</p>
                <p className="text-xs text-gray-500 mb-2">背景：{question.background}</p>
                <div className="flex flex-wrap gap-1">
                  {question.assumptions.map((assumption, i) => (
                    <span key={i} className="px-2 py-1 text-xs bg-primary-50 text-primary-600 rounded">
                      假设 {i + 1}: {assumption}
                    </span>
                  ))}
                </div>
              </div>
            ))
          ) : (
            <p className="text-sm text-gray-500 italic">暂无数据</p>
          )}
        </div>
      </div>
    </div>
  );
}
