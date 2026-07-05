'use client';

import { useState } from 'react';
import Header from '@/components/Header';
import SearchInput from '@/components/SearchInput';
import PaperTable from '@/components/PaperTable';
import GapAnalysis from '@/components/GapAnalysis';
import ResearchHistory from '@/components/ResearchHistory';
import type { ResearchSettings } from '@/components/Header';

interface Paper {
  id: string;
  title: string;
  authors: string[];
  year: string;
  source: string;
  url: string;
  abstract: string;
}

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

interface AnalysisResult {
  papers: Paper[];
  solved_problems: SolvedProblem[];
  research_gaps: Gap[];
  research_questions: ResearchQuestion[];
}

export default function Home() {
  const [isLoading, setIsLoading] = useState(false);
  const [topic, setTopic] = useState('');
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [error, setError] = useState<string>('');
  const [progress, setProgress] = useState<string>('');
  const [refreshKey, setRefreshKey] = useState(0);
  const [activeSessionId, setActiveSessionId] = useState<string>('');
  const [myPapers, setMyPapers] = useState<Paper[]>([]);
  const [settings, setSettings] = useState<ResearchSettings>({
    venues: ['NeurIPS','ICML','ICLR','AAAI','CVPR','ICCV','ACL','EMNLP','OSDI','SOSP','NSDI','SIGCOMM'],
    maxPapers: 5,
    yearStart: 2020,
    yearEnd: 2026,
  });

  const handleNew = () => {
    setResult(null);
    setTopic('');
    setError('');
    setActiveSessionId('');
    setMyPapers([]);
  };

  const viewSession = async (sessionId: string) => {
    try {
      const res = await fetch(`/api/report/${sessionId}`);
      const data = await res.json();
      if (data.success && data.report) {
        setResult(parseReport(data.report));
      }
      const hRes = await fetch(`/api/history/${sessionId}`);
      const hData = await hRes.json();
      if (hData.session) {
        setTopic(hData.session.topic);
        setActiveSessionId(sessionId);
      }
    } catch (e) {
      console.error('Failed to load session:', e);
    }
  };

  const handleSearch = async (searchTopic: string) => {
    setTopic(searchTopic);
    setIsLoading(true);
    setResult(null);
    setError('');
    setActiveSessionId('');

    try {
      const response = await fetch('/api/query', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic: searchTopic, max_papers: settings.maxPapers, venues: settings.venues, year_start: settings.yearStart, year_end: settings.yearEnd }),
      });

      if (!response.ok) throw new Error(`API returned ${response.status}`);

      const data = await response.json();
      if (data.task_id) {
        await pollForResults(data.task_id);
      } else {
        setError('Server returned no task ID');
      }
    } catch (error: any) {
      console.error('Error:', error);
      setError(`Request failed: ${error.message || 'Unknown error'}. Check that the backend is running.`);
    } finally {
      setIsLoading(false);
      setRefreshKey(k => k + 1);
    }
  };

  const pollForResults = async (taskId: string) => {
    let attempts = 0;
    const maxAttempts = 450;
    const delay = 2000;

    while (attempts < maxAttempts) {
      try {
        const response = await fetch(`/api/status/${taskId}`);
        const statusData = await response.json();

        const msg = statusData.message || '';
        if (msg) setProgress(msg);

        if (statusData.status === 'completed') {
          const reportResponse = await fetch(`/api/report/${taskId}`);
          const reportData = await reportResponse.json();

          if (reportData.success && reportData.report) {
            setResult(parseReport(reportData.report));
            setActiveSessionId(taskId);
          } else {
            setError('Report parsing failed');
          }
          return;
        } else if (statusData.status === 'failed') {
          setError(`Research failed: ${statusData.message || 'unknown'}`);
          return;
        }
      } catch (error: any) {
        console.error('Polling error:', error);
      }

      attempts++;
      await new Promise(resolve => setTimeout(resolve, delay));
    }

    // One last check
    try {
      const res = await fetch(`/api/status/${taskId}`);
      const last = await res.json();
      if (last.status === 'completed') {
        const rep = await fetch(`/api/report/${taskId}`);
        const repData = await rep.json();
        if (repData.success && repData.report) {
          setResult(parseReport(repData.report));
          setActiveSessionId(taskId);
          return;
        }
      }
    } catch (_) {}

    setError(`Research timed out (${Math.round(maxAttempts * delay / 1000)} seconds). Try again or reduce paper count.`);
  };

  const parseReport = (report: any): AnalysisResult => {
    if (!report.content) return { papers: [], solved_problems: [], research_gaps: [], research_questions: [] };
    try {
      const content = report.content;
      let papers: Paper[] = [];
      if (content['papers_table.json']) {
        const tableData = JSON.parse(content['papers_table.json']);
        papers = tableData.papers || [];
      }
      let solved_problems: SolvedProblem[] = [];
      let research_gaps: Gap[] = [];
      let research_questions: ResearchQuestion[] = [];
      if (content['final_gap.json']) {
        const gapData = JSON.parse(content['final_gap.json']);
        solved_problems = gapData.solved_problems || [];
        research_gaps = gapData.research_gaps || [];
        research_questions = gapData.research_questions || [];
      }
      return { papers, solved_problems, research_gaps, research_questions };
    } catch {
      return { papers: [], solved_problems: [], research_gaps: [], research_questions: [] };
    }
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header settings={settings} onSettingsChange={setSettings} />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex gap-6">
          {/* Left column */}
          <div className="flex-1 min-w-0">
            <SearchInput onSearch={handleSearch} isLoading={isLoading} progressMessage={progress} />

            {error && (
              <div className="mt-4 bg-red-50 border border-red-200 rounded-lg p-4 text-red-700">
                <div className="flex items-center gap-2">
                  <span className="font-medium">{error}</span>
                </div>
              </div>
            )}

            {/* Paper list — always visible, shows research results + uploaded PDFs */}
            <div className="mt-8">
              <PaperTable
                papers={[...(result?.papers || []), ...myPapers]}
                onPaperAdded={(paper) => setMyPapers(prev => [...prev, paper])}
              />
            </div>

            {result && (
              <div className="space-y-8 mt-8">
                <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="text-xl font-bold text-gray-900">研究主题</h2>
                      <p className="text-gray-500 mt-1">{topic}</p>
                    </div>
                    <div className="flex items-center space-x-4">
                      <span className="px-3 py-1 bg-primary-100 text-primary-600 text-sm rounded-full">
                        {result.papers.length} 篇论文
                      </span>
                      <span className="px-3 py-1 bg-warning/10 text-warning text-sm rounded-full">
                        {result.research_gaps.length} 个研究空白
                      </span>
                    </div>
                  </div>
                </div>

                <GapAnalysis
                  solved_problems={result.solved_problems}
                  research_gaps={result.research_gaps}
                  research_questions={result.research_questions}
                />
              </div>
            )}

            {!result && !isLoading && (
              <div className="text-center py-16 mt-8">
                <div className="inline-flex items-center justify-center w-20 h-20 bg-gray-100 rounded-full mb-4">
                  <svg className="w-10 h-10 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4" />
                  </svg>
                </div>
                <h3 className="text-lg font-semibold text-gray-900 mb-2">开始您的研究</h3>
                <p className="text-gray-500 max-w-md mx-auto">
                  输入研究主题，AI 将帮助您搜索论文、分析研究空白并提出研究问题
                </p>
              </div>
            )}
          </div>

          {/* Right sidebar */}
          <div className="w-72 flex-shrink-0 space-y-4">
            <ResearchHistory onSelect={viewSession} onNew={handleNew} refreshTrigger={refreshKey} activeId={activeSessionId} />
          </div>
        </div>
      </main>
    </div>
  );
}
