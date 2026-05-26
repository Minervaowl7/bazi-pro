import { useEffect, useCallback } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { Download, Share2, Loader2, CheckCircle, XCircle, ArrowLeft } from 'lucide-react';
import { api } from '../api/client';
import { useAnalysisStore } from '../store/analysisStore';

export default function ResultPage() {
  const { runId } = useParams<{ runId: string }>();
  const navigate = useNavigate();
  const {
    status,
    progress,
    currentStep,
    wsConnected,
    resultHtml,
    error,
    connectWs,
    disconnectWs,
    setProgress,
    setResult,
    setError,
    reset,
  } = useAnalysisStore();

  const fetchResult = useCallback(async () => {
    if (!runId) return;
    try {
      const res = await api.analysis.result(runId);
      if (res.status === 'completed') {
        const htmlStr = (res as unknown as Record<string, unknown>).html as string | undefined;
        if (htmlStr) {
          setResult(htmlStr);
        } else {
          setResult(JSON.stringify(res, null, 2));
        }
      }
    } catch (err) {
      setError((err as Error).message);
    }
  }, [runId, setResult, setError]);

  const pollStatus = useCallback(async () => {
    if (!runId) return;
    try {
      const res = await api.analysis.status(runId);
      if (res.step !== undefined && res.summary) {
        setProgress(res.step, res.summary, res.status);
      }
      if (res.status === 'completed') {
        await fetchResult();
      } else if (res.status === 'failed') {
        setError(res.error || '分析失败');
      }
    } catch {
      // will retry
    }
  }, [runId, setProgress, fetchResult, setError]);

  useEffect(() => {
    if (!runId) return;

    if (status === 'idle' || status === 'queued') {
      connectWs(runId);
    }

    return () => {
      disconnectWs();
    };
  }, [runId]);

  useEffect(() => {
    if (status === 'running' || status === 'queued') {
      const interval = setInterval(pollStatus, 3000);
      return () => clearInterval(interval);
    }
  }, [status, pollStatus]);

  useEffect(() => {
    return () => {
      reset();
    };
  }, [reset]);

  const handleDownload = () => {
    if (!resultHtml) return;
    const blob = new Blob([resultHtml], { type: 'text/html;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `bazi-report-${runId}.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const handleShare = async () => {
    if (!runId) return;
    const shareUrl = `${window.location.origin}/result/${runId}`;
    if (navigator.share) {
      try {
        await navigator.share({ title: '八字命理分析报告', url: shareUrl });
      } catch {
        // user cancelled
      }
    } else {
      await navigator.clipboard.writeText(shareUrl);
      alert('链接已复制到剪贴板');
    }
  };

  const steps = [
    '解析八字',
    '得令评估',
    '得地评估',
    '得势评估',
    '旺衰判定',
    '格局分析',
    '用神推导',
    '生成报告',
    '分析完成',
  ];

  return (
    <div className="p-4 sm:p-8 max-w-4xl mx-auto">
      <button
        onClick={() => navigate('/analyze')}
        className="flex items-center gap-2 text-ink-muted hover:text-ink-text transition-colors mb-6"
      >
        <ArrowLeft size={18} />
        <span className="text-sm">返回分析</span>
      </button>

      {status !== 'completed' && status !== 'failed' && (
        <div className="bg-ink-light border border-ink-border rounded-xl p-6 sm:p-8 mb-6">
          <div className="flex items-center gap-3 mb-6">
            <Loader2 size={24} className="animate-spin text-gold" />
            <div>
              <h2 className="font-display text-lg text-ink-text">分析进行中</h2>
              <p className="text-ink-muted text-sm">
                {currentStep || '正在准备...'}
                {wsConnected && (
                  <span className="ml-2 text-green-400 text-xs">● 实时连接</span>
                )}
              </p>
            </div>
          </div>

          <div className="mb-6">
            <div className="flex justify-between text-xs text-ink-muted mb-2">
              <span>进度</span>
              <span>{Math.round(progress)}%</span>
            </div>
            <div className="w-full h-2 bg-ink rounded-full overflow-hidden">
              <div
                className="h-full bg-gradient-to-r from-vermilion to-gold rounded-full transition-all duration-500 ease-out"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>

          <div className="space-y-2">
            {steps.map((step, index) => {
              const stepProgress = ((index + 1) / steps.length) * 100;
              const isDone = progress >= stepProgress;
              const isCurrent = progress >= (index / steps.length) * 100 && progress < stepProgress;
              return (
                <div
                  key={index}
                  className={`flex items-center gap-3 text-sm py-1.5 px-3 rounded-lg transition-all ${
                    isDone
                      ? 'text-gold'
                      : isCurrent
                        ? 'text-ink-text bg-ink-lighter'
                        : 'text-ink-muted/50'
                  }`}
                >
                  {isDone ? (
                    <CheckCircle size={16} className="text-gold shrink-0" />
                  ) : isCurrent ? (
                    <Loader2 size={16} className="animate-spin text-gold shrink-0" />
                  ) : (
                    <div className="w-4 h-4 rounded-full border border-ink-border shrink-0" />
                  )}
                  <span>{step}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {status === 'failed' && (
        <div className="bg-ink-light border border-vermilion/30 rounded-xl p-6 sm:p-8 mb-6">
          <div className="flex items-center gap-3 mb-4">
            <XCircle size={24} className="text-vermilion" />
            <h2 className="font-display text-lg text-vermilion">分析失败</h2>
          </div>
          <p className="text-ink-muted text-sm">{error || '分析过程中发生错误，请重试'}</p>
          <button
            onClick={() => navigate('/analyze')}
            className="mt-4 px-6 py-2 bg-vermilion hover:bg-vermilion-dark text-rice rounded-lg text-sm transition-all"
          >
            重新分析
          </button>
        </div>
      )}

      {status === 'completed' && resultHtml && (
        <div className="animate-fade-in">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <CheckCircle size={20} className="text-gold" />
              <h2 className="font-display text-lg text-gold">分析报告</h2>
            </div>
            <div className="flex gap-2">
              <button
                onClick={handleDownload}
                className="flex items-center gap-1.5 px-4 py-2 bg-ink-light border border-ink-border rounded-lg text-sm text-ink-muted hover:text-ink-text hover:border-ink-muted transition-all"
              >
                <Download size={16} />
                下载
              </button>
              <button
                onClick={handleShare}
                className="flex items-center gap-1.5 px-4 py-2 bg-ink-light border border-ink-border rounded-lg text-sm text-ink-muted hover:text-ink-text hover:border-ink-muted transition-all"
              >
                <Share2 size={16} />
                分享
              </button>
            </div>
          </div>

          <div className="bg-rice rounded-xl overflow-hidden border border-ink-border">
            <iframe
              srcDoc={resultHtml}
              title="八字命理分析报告"
              className="w-full border-0"
              style={{ minHeight: '80vh' }}
              sandbox="allow-same-origin"
            />
          </div>
        </div>
      )}

      {status === 'completed' && !resultHtml && (
        <div className="bg-ink-light border border-ink-border rounded-xl p-6 sm:p-8">
          <div className="flex items-center gap-3 mb-4">
            <CheckCircle size={24} className="text-gold" />
            <h2 className="font-display text-lg text-gold">分析完成</h2>
          </div>
          <p className="text-ink-muted text-sm mb-4">正在加载报告...</p>
          <button
            onClick={fetchResult}
            className="px-6 py-2 bg-gold/20 text-gold rounded-lg text-sm hover:bg-gold/30 transition-all"
          >
            重新加载
          </button>
        </div>
      )}
    </div>
  );
}
