import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Eye, EyeOff } from 'lucide-react';
import { useAuthStore } from '../store/authStore';

export default function RegisterPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [displayName, setDisplayName] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [localError, setLocalError] = useState('');
  const register = useAuthStore((s) => s.register);
  const loading = useAuthStore((s) => s.loading);
  const error = useAuthStore((s) => s.error);
  const clearError = useAuthStore((s) => s.clearError);
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    clearError();
    setLocalError('');

    if (password !== confirmPassword) {
      setLocalError('两次输入的密码不一致');
      return;
    }

    if (password.length < 6) {
      setLocalError('密码长度至少6位');
      return;
    }

    try {
      await register(email, password, displayName || undefined);
      navigate('/analyze');
    } catch {
      // error is set in store
    }
  };

  const displayError = localError || error;

  return (
    <div className="min-h-screen flex">
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden bg-ink-light items-center justify-center">
        <div className="absolute inset-0 opacity-10">
          <svg viewBox="0 0 400 400" className="w-full h-full">
            <defs>
              <pattern id="grid2" width="40" height="40" patternUnits="userSpaceOnUse">
                <path d="M 40 0 L 0 0 0 40" fill="none" stroke="currentColor" strokeWidth="0.5" className="text-gold" />
              </pattern>
            </defs>
            <rect width="400" height="400" fill="url(#grid2)" />
          </svg>
        </div>
        <div className="relative z-10 text-center px-12">
          <div className="mb-8">
            <svg viewBox="0 0 120 120" className="w-32 h-32 mx-auto text-gold/40">
              <circle cx="60" cy="60" r="55" fill="none" stroke="currentColor" strokeWidth="1" />
              <circle cx="60" cy="60" r="40" fill="none" stroke="currentColor" strokeWidth="0.5" />
              <circle cx="60" cy="60" r="25" fill="none" stroke="currentColor" strokeWidth="0.5" />
              <line x1="60" y1="5" x2="60" y2="115" stroke="currentColor" strokeWidth="0.5" />
              <line x1="5" y1="60" x2="115" y2="60" stroke="currentColor" strokeWidth="0.5" />
              <circle cx="60" cy="60" r="3" fill="currentColor" />
              <text x="60" y="18" textAnchor="middle" className="fill-current text-[8px]">午</text>
              <text x="60" y="108" textAnchor="middle" className="fill-current text-[8px]">子</text>
              <text x="108" y="63" textAnchor="middle" className="fill-current text-[8px]">卯</text>
              <text x="12" y="63" textAnchor="middle" className="fill-current text-[8px]">酉</text>
            </svg>
          </div>
          <h2 className="font-display text-4xl text-gold tracking-[0.3em] mb-4">
            八字命理
          </h2>
          <p className="text-ink-muted text-sm leading-relaxed max-w-xs mx-auto">
            探索命理奥秘，洞悉天地玄机。注册账户，开启您的命理之旅。
          </p>
          <div className="mt-8 flex justify-center gap-2">
            {['子', '丑', '寅', '卯', '辰', '巳', '午', '未', '申', '酉', '戌', '亥'].map((zhi) => (
              <span key={zhi} className="text-gold/30 font-display text-sm">{zhi}</span>
            ))}
          </div>
        </div>
      </div>

      <div className="w-full lg:w-1/2 flex items-center justify-center p-6 sm:p-12 bg-ink">
        <div className="w-full max-w-md animate-fade-in">
          <div className="lg:hidden text-center mb-8">
            <h1 className="font-display text-3xl text-gold tracking-[0.3em]">八字命理</h1>
            <p className="text-ink-muted text-xs mt-1 tracking-wider">BAZI-PRO</p>
          </div>

          <h2 className="font-display text-2xl text-ink-text mb-2">注册</h2>
          <p className="text-ink-muted text-sm mb-8">创建账户，探索命理世界</p>

          {displayError && (
            <div className="mb-4 p-3 bg-vermilion/10 border border-vermilion/30 rounded-lg text-vermilion text-sm">
              {displayError}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label className="block text-sm text-ink-muted mb-1.5">邮箱地址</label>
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                className="w-full px-4 py-3 bg-ink-light border border-ink-border rounded-lg text-ink-text placeholder-ink-muted/50 focus:outline-none focus:border-gold/50 focus:ring-1 focus:ring-gold/20 transition-all"
                placeholder="请输入邮箱"
              />
            </div>

            <div>
              <label className="block text-sm text-ink-muted mb-1.5">显示名称</label>
              <input
                type="text"
                value={displayName}
                onChange={(e) => setDisplayName(e.target.value)}
                className="w-full px-4 py-3 bg-ink-light border border-ink-border rounded-lg text-ink-text placeholder-ink-muted/50 focus:outline-none focus:border-gold/50 focus:ring-1 focus:ring-gold/20 transition-all"
                placeholder="可选，用于显示"
              />
            </div>

            <div>
              <label className="block text-sm text-ink-muted mb-1.5">密码</label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={6}
                  className="w-full px-4 py-3 bg-ink-light border border-ink-border rounded-lg text-ink-text placeholder-ink-muted/50 focus:outline-none focus:border-gold/50 focus:ring-1 focus:ring-gold/20 transition-all pr-12"
                  placeholder="至少6位密码"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-ink-muted hover:text-ink-text transition-colors"
                >
                  {showPassword ? <EyeOff size={18} /> : <Eye size={18} />}
                </button>
              </div>
            </div>

            <div>
              <label className="block text-sm text-ink-muted mb-1.5">确认密码</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                className="w-full px-4 py-3 bg-ink-light border border-ink-border rounded-lg text-ink-text placeholder-ink-muted/50 focus:outline-none focus:border-gold/50 focus:ring-1 focus:ring-gold/20 transition-all"
                placeholder="再次输入密码"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-vermilion hover:bg-vermilion-dark text-rice font-medium rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? '注册中...' : '注册'}
            </button>
          </form>

          <p className="mt-8 text-center text-sm text-ink-muted">
            已有账户？{' '}
            <Link to="/login" className="text-gold hover:text-gold-light transition-colors">
              立即登录
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
