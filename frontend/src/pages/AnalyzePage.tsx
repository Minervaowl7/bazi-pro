import { useState, type FormEvent } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, Loader2 } from 'lucide-react';
import { api } from '../api/client';
import { useAnalysisStore } from '../store/analysisStore';

const TIANGAN = ['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸'];
const DIZHI = ['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'];

const DETAIL_LEVELS = [
  { value: 'brief', label: '简要分析', desc: '快速概览命盘要点' },
  { value: 'standard', label: '标准分析', desc: '全面解读四柱格局' },
  { value: 'detailed', label: '深度分析', desc: '详尽剖析命理玄机' },
];

interface PillarState {
  gan: string;
  zhi: string;
}

export default function AnalyzePage() {
  const [pillars, setPillars] = useState<PillarState[]>([
    { gan: '', zhi: '' },
    { gan: '', zhi: '' },
    { gan: '', zhi: '' },
    { gan: '', zhi: '' },
  ]);
  const [gender, setGender] = useState('');
  const [solarDate, setSolarDate] = useState('');
  const [detailLevel, setDetailLevel] = useState('standard');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');
  const startAnalysis = useAnalysisStore((s) => s.startAnalysis);
  const navigate = useNavigate();

  const pillarLabels = ['年柱', '月柱', '日柱', '日柱'];

  const updatePillar = (index: number, field: 'gan' | 'zhi', value: string) => {
    const updated = [...pillars];
    updated[index] = { ...updated[index], [field]: value };
    setPillars(updated);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    setError('');

    if (!gender) {
      setError('请选择性别');
      return;
    }

    for (let i = 0; i < 4; i++) {
      if (!pillars[i].gan || !pillars[i].zhi) {
        setError(`请完善${pillarLabels[i]}的天干地支`);
        return;
      }
    }

    const baziStr = pillars.map((p) => `${p.gan}${p.zhi}`).join(' ');
    const dayMaster = pillars[2].gan;

    setSubmitting(true);
    try {
      const res = await api.analysis.create({
        性别: gender,
        八字: baziStr,
        日主: dayMaster,
        detail_level: detailLevel,
        阳历: solarDate || undefined,
      });
      startAnalysis(res.run_id);
      navigate(`/result/${res.run_id}`);
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="p-4 sm:p-8 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="font-display text-2xl sm:text-3xl text-gold tracking-wider mb-2">
          命盘分析
        </h1>
        <p className="text-ink-muted text-sm">输入八字信息，开启命理解读</p>
      </div>

      {error && (
        <div className="mb-6 p-3 bg-vermilion/10 border border-vermilion/30 rounded-lg text-vermilion text-sm">
          {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="bg-ink-light border border-ink-border rounded-xl p-6 sm:p-8 mb-6">
          <h2 className="font-display text-lg text-gold mb-6">四柱八字</h2>

          <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 sm:gap-6">
            {pillars.map((pillar, index) => (
              <div key={index} className="text-center">
                <label className="block text-sm text-ink-muted mb-3">
                  {['年柱', '月柱', '日柱', '时柱'][index]}
                </label>
                <div className="space-y-3">
                  <select
                    value={pillar.gan}
                    onChange={(e) => updatePillar(index, 'gan', e.target.value)}
                    className="w-full px-3 py-2.5 bg-ink border border-ink-border rounded-lg text-ink-text text-center font-display text-lg focus:outline-none focus:border-gold/50 focus:ring-1 focus:ring-gold/20 transition-all appearance-none cursor-pointer"
                  >
                    <option value="" disabled>天干</option>
                    {TIANGAN.map((g) => (
                      <option key={g} value={g}>{g}</option>
                    ))}
                  </select>
                  <select
                    value={pillar.zhi}
                    onChange={(e) => updatePillar(index, 'zhi', e.target.value)}
                    className="w-full px-3 py-2.5 bg-ink border border-ink-border rounded-lg text-ink-text text-center font-display text-lg focus:outline-none focus:border-gold/50 focus:ring-1 focus:ring-gold/20 transition-all appearance-none cursor-pointer"
                  >
                    <option value="" disabled>地支</option>
                    {DIZHI.map((z) => (
                      <option key={z} value={z}>{z}</option>
                    ))}
                  </select>
                </div>
                {pillar.gan && pillar.zhi && (
                  <div className="mt-3 py-2 bg-ink-lighter rounded-lg">
                    <span className="font-display text-xl text-gold">
                      {pillar.gan}{pillar.zhi}
                    </span>
                  </div>
                )}
              </div>
            ))}
          </div>

          {pillars.every((p) => p.gan && p.zhi) && (
            <div className="mt-6 pt-4 border-t border-ink-border text-center">
              <span className="text-ink-muted text-sm">八字：</span>
              <span className="font-display text-lg text-gold tracking-widest ml-2">
                {pillars.map((p) => `${p.gan}${p.zhi}`).join(' ')}
              </span>
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-6">
          <div className="bg-ink-light border border-ink-border rounded-xl p-6">
            <h2 className="font-display text-lg text-gold mb-4">性别</h2>
            <div className="flex gap-3">
              {['男', '女', '其他'].map((g) => (
                <button
                  key={g}
                  type="button"
                  onClick={() => setGender(g)}
                  className={`flex-1 py-2.5 rounded-lg text-sm font-medium transition-all duration-200 ${
                    gender === g
                      ? 'bg-vermilion text-rice'
                      : 'bg-ink border border-ink-border text-ink-muted hover:text-ink-text hover:border-ink-muted'
                  }`}
                >
                  {g}
                </button>
              ))}
            </div>
          </div>

          <div className="bg-ink-light border border-ink-border rounded-xl p-6">
            <h2 className="font-display text-lg text-gold mb-4">出生日期</h2>
            <input
              type="date"
              value={solarDate}
              onChange={(e) => setSolarDate(e.target.value)}
              className="w-full px-4 py-2.5 bg-ink border border-ink-border rounded-lg text-ink-text focus:outline-none focus:border-gold/50 focus:ring-1 focus:ring-gold/20 transition-all"
            />
          </div>
        </div>

        <div className="bg-ink-light border border-ink-border rounded-xl p-6 sm:p-8 mb-8">
          <h2 className="font-display text-lg text-gold mb-4">分析深度</h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {DETAIL_LEVELS.map((level) => (
              <button
                key={level.value}
                type="button"
                onClick={() => setDetailLevel(level.value)}
                className={`p-4 rounded-xl text-left transition-all duration-200 ${
                  detailLevel === level.value
                    ? 'bg-gold/10 border-2 border-gold/50'
                    : 'bg-ink border border-ink-border hover:border-ink-muted'
                }`}
              >
                <div className={`font-display text-base mb-1 ${
                  detailLevel === level.value ? 'text-gold' : 'text-ink-text'
                }`}>
                  {level.label}
                </div>
                <div className="text-xs text-ink-muted">{level.desc}</div>
              </button>
            ))}
          </div>
        </div>

        <button
          type="submit"
          disabled={submitting}
          className="w-full py-4 bg-vermilion hover:bg-vermilion-dark text-rice font-display text-lg tracking-wider rounded-xl transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
        >
          {submitting ? (
            <>
              <Loader2 size={20} className="animate-spin" />
              提交中...
            </>
          ) : (
            <>
              <Sparkles size={20} />
              开始分析
            </>
          )}
        </button>
      </form>
    </div>
  );
}
