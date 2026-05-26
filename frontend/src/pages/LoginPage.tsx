import { useState, type FormEvent } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { MessageCircle, Eye, EyeOff } from 'lucide-react';
import { useAuthStore } from '../store/authStore';

export default function LoginPage() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const login = useAuthStore((s) => s.login);
  const loading = useAuthStore((s) => s.loading);
  const error = useAuthStore((s) => s.error);
  const clearError = useAuthStore((s) => s.clearError);
  const navigate = useNavigate();

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    clearError();
    try {
      await login(email, password);
      navigate('/analyze');
    } catch {
      // error is set in store
    }
  };

  const handleWechatLogin = () => {
    const appId = import.meta.env.VITE_WECHAT_APP_ID;
    if (!appId) {
      alert('微信登录未配置');
      return;
    }
    const redirectUri = encodeURIComponent(window.location.origin + '/login');
    window.location.href = `https://open.weixin.qq.com/connect/qrconnect?appid=${appId}&redirect_uri=${redirectUri}&response_type=code&scope=snsapi_login#wechat_redirect`;
  };

  return (
    <div className="min-h-screen flex">
      <div className="hidden lg:flex lg:w-1/2 relative overflow-hidden bg-ink-light items-center justify-center">
        <div className="absolute inset-0 opacity-10">
          <svg viewBox="0 0 400 400" className="w-full h-full">
            <defs>
              <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
                <path d="M 40 0 L 0 0 0 40" fill="none" stroke="currentColor" strokeWidth="0.5" className="text-gold" />
              </pattern>
            </defs>
            <rect width="400" height="400" fill="url(#grid)" />
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
            天行有常，命理可循。以古法为基，借今术为用，解读四柱之玄机。
          </p>
          <div className="mt-8 flex justify-center gap-2">
            {['甲', '乙', '丙', '丁', '戊', '己', '庚', '辛', '壬', '癸'].map((gan) => (
              <span key={gan} className="text-gold/30 font-display text-sm">{gan}</span>
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

          <h2 className="font-display text-2xl text-ink-text mb-2">登录</h2>
          <p className="text-ink-muted text-sm mb-8">登录您的账户，开始命理分析</p>

          {error && (
            <div className="mb-4 p-3 bg-vermilion/10 border border-vermilion/30 rounded-lg text-vermilion text-sm">
              {error}
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
              <label className="block text-sm text-ink-muted mb-1.5">密码</label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  minLength={6}
                  className="w-full px-4 py-3 bg-ink-light border border-ink-border rounded-lg text-ink-text placeholder-ink-muted/50 focus:outline-none focus:border-gold/50 focus:ring-1 focus:ring-gold/20 transition-all pr-12"
                  placeholder="请输入密码"
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

            <button
              type="submit"
              disabled={loading}
              className="w-full py-3 bg-vermilion hover:bg-vermilion-dark text-rice font-medium rounded-lg transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? '登录中...' : '登录'}
            </button>
          </form>

          <div className="mt-6">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-ink-border" />
              </div>
              <div className="relative flex justify-center text-xs">
                <span className="px-4 bg-ink text-ink-muted">其他登录方式</span>
              </div>
            </div>

            <button
              onClick={handleWechatLogin}
              className="mt-4 w-full py-3 border border-ink-border rounded-lg text-ink-text hover:bg-ink-lighter transition-all duration-200 flex items-center justify-center gap-2"
            >
              <MessageCircle size={18} className="text-green-500" />
              微信登录
            </button>
          </div>

          <p className="mt-8 text-center text-sm text-ink-muted">
            还没有账户？{' '}
            <Link to="/register" className="text-gold hover:text-gold-light transition-colors">
              立即注册
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
