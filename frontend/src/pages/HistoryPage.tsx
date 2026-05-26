import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Clock, Eye, ChevronLeft, ChevronRight, Loader2 } from 'lucide-react';
import { api, type HistoryItem } from '../api/client';

const PAGE_SIZE = 10;

const statusMap: Record<string, { label: string; color: string }> = {
  completed: { label: '已完成', color: 'text-gold' },
  running: { label: '进行中', color: 'text-blue-400' },
  queued: { label: '排队中', color: 'text-ink-muted' },
  failed: { label: '失败', color: 'text-vermilion' },
};

export default function HistoryPage() {
  const [records, setRecords] = useState<HistoryItem[]>([]);
  const [total, setTotal] = useState(0);
  const [offset, setOffset] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const navigate = useNavigate();

  const fetchHistory = async (newOffset: number) => {
    setLoading(true);
    setError('');
    try {
      const res = await api.history.list(PAGE_SIZE, newOffset);
      setRecords(res.history);
      setTotal(res.total);
      setOffset(newOffset);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHistory(0);
  }, []);

  const formatDate = (dateStr: string) => {
    try {
      const d = new Date(dateStr);
      return d.toLocaleString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit',
      });
    } catch {
      return dateStr;
    }
  };

  const totalPages = Math.ceil(total / PAGE_SIZE);
  const currentPage = Math.floor(offset / PAGE_SIZE) + 1;

  return (
    <div className="p-4 sm:p-8 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="font-display text-2xl sm:text-3xl text-gold tracking-wider mb-2">
          历史记录
        </h1>
        <p className="text-ink-muted text-sm">查看您的命理分析历史</p>
      </div>

      {error && (
        <div className="mb-6 p-3 bg-vermilion/10 border border-vermilion/30 rounded-lg text-vermilion text-sm">
          {error}
        </div>
      )}

      {loading ? (
        <div className="flex items-center justify-center py-20">
          <Loader2 size={32} className="animate-spin text-gold" />
        </div>
      ) : records.length === 0 ? (
        <div className="bg-ink-light border border-ink-border rounded-xl p-12 text-center">
          <Clock size={48} className="mx-auto text-ink-muted/30 mb-4" />
          <p className="text-ink-muted mb-4">暂无分析记录</p>
          <button
            onClick={() => navigate('/analyze')}
            className="px-6 py-2 bg-vermilion hover:bg-vermilion-dark text-rice rounded-lg text-sm transition-all"
          >
            开始分析
          </button>
        </div>
      ) : (
        <>
          <div className="space-y-3">
            {records.map((record) => {
              const statusInfo = statusMap[record.status] || { label: record.status, color: 'text-ink-muted' };
              return (
                <div
                  key={record.run_id}
                  className="bg-ink-light border border-ink-border rounded-xl p-4 sm:p-5 hover:border-ink-muted/50 transition-all"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-3 mb-2">
                        <span className="font-display text-lg text-gold tracking-wider">
                          {record.bazi || '—'}
                        </span>
                        <span className={`text-xs px-2 py-0.5 rounded-full bg-ink-lighter ${statusInfo.color}`}>
                          {statusInfo.label}
                        </span>
                      </div>
                      <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-ink-muted">
                        {record.gender && <span>性别：{record.gender}</span>}
                        {record.day_master && <span>日主：{record.day_master}</span>}
                        {record.solar_date && <span>日期：{record.solar_date}</span>}
                        {record.detail_level && <span>深度：{record.detail_level}</span>}
                      </div>
                      <div className="mt-2 text-xs text-ink-muted/60">
                        {record.created_at ? formatDate(record.created_at) : ''}
                      </div>
                    </div>
                    {record.status === 'completed' && (
                      <button
                        onClick={() => navigate(`/result/${record.run_id}`)}
                        className="flex items-center gap-1.5 px-3 py-1.5 bg-ink border border-ink-border rounded-lg text-sm text-ink-muted hover:text-gold hover:border-gold/30 transition-all shrink-0"
                      >
                        <Eye size={14} />
                        查看
                      </button>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-center gap-4 mt-8">
              <button
                onClick={() => fetchHistory(Math.max(0, offset - PAGE_SIZE))}
                disabled={offset === 0}
                className="flex items-center gap-1 px-3 py-2 bg-ink-light border border-ink-border rounded-lg text-sm text-ink-muted hover:text-ink-text disabled:opacity-30 disabled:cursor-not-allowed transition-all"
              >
                <ChevronLeft size={16} />
                上一页
              </button>
              <span className="text-sm text-ink-muted">
                {currentPage} / {totalPages}
              </span>
              <button
                onClick={() => fetchHistory(offset + PAGE_SIZE)}
                disabled={currentPage >= totalPages}
                className="flex items-center gap-1 px-3 py-2 bg-ink-light border border-ink-border rounded-lg text-sm text-ink-muted hover:text-ink-text disabled:opacity-30 disabled:cursor-not-allowed transition-all"
              >
                下一页
                <ChevronRight size={16} />
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
