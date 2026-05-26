import { useEffect, useState } from 'react';
import { User, CreditCard, Crown, Loader2, Shield } from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import { api, type QuotaInfo, type SubscriptionInfo } from '../api/client';

export default function AccountPage() {
  const user = useAuthStore((s) => s.user);
  const fetchUser = useAuthStore((s) => s.fetchUser);
  const [quota, setQuota] = useState<QuotaInfo | null>(null);
  const [subscription, setSubscription] = useState<SubscriptionInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [changingPassword, setChangingPassword] = useState(false);
  const [oldPassword, setOldPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmNewPassword, setConfirmNewPassword] = useState('');
  const [passwordMsg, setPasswordMsg] = useState('');

  useEffect(() => {
    fetchUser();
  }, [fetchUser]);

  useEffect(() => {
    if (!user?.id) return;
    const fetchBilling = async () => {
      setLoading(true);
      try {
        const [quotaRes, subRes] = await Promise.allSettled([
          api.billing.quota(user.id),
          api.billing.subscription(user.id),
        ]);
        if (quotaRes.status === 'fulfilled') setQuota(quotaRes.value);
        if (subRes.status === 'fulfilled') setSubscription(subRes.value);
      } catch {
        // ignore
      } finally {
        setLoading(false);
      }
    };
    fetchBilling();
  }, [user?.id]);

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    setPasswordMsg('');
    if (newPassword !== confirmNewPassword) {
      setPasswordMsg('两次输入的新密码不一致');
      return;
    }
    if (newPassword.length < 6) {
      setPasswordMsg('密码长度至少6位');
      return;
    }
    setChangingPassword(true);
    try {
      // Note: backend doesn't have a change-password endpoint yet,
      // this is a placeholder for future implementation
      setPasswordMsg('密码修改功能即将上线');
    } catch {
      setPasswordMsg('密码修改失败，请稍后重试');
    } finally {
      setChangingPassword(false);
    }
  };

  const planLabels: Record<string, string> = {
    free: '免费版',
    basic: '基础版',
    pro: '专业版',
    premium: '尊享版',
  };

  return (
    <div className="p-4 sm:p-8 max-w-4xl mx-auto">
      <div className="mb-8">
        <h1 className="font-display text-2xl sm:text-3xl text-gold tracking-wider mb-2">
          我的账户
        </h1>
        <p className="text-ink-muted text-sm">管理您的账户信息和订阅</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-ink-light border border-ink-border rounded-xl p-6">
          <div className="flex items-center gap-3 mb-6">
            <User size={20} className="text-gold" />
            <h2 className="font-display text-lg text-gold">个人信息</h2>
          </div>

          <div className="space-y-4">
            <div>
              <label className="block text-xs text-ink-muted mb-1">邮箱</label>
              <p className="text-ink-text">{user?.email || '—'}</p>
            </div>
            <div>
              <label className="block text-xs text-ink-muted mb-1">显示名称</label>
              <p className="text-ink-text">{user?.display_name || '未设置'}</p>
            </div>
            <div>
              <label className="block text-xs text-ink-muted mb-1">注册时间</label>
              <p className="text-ink-text">
                {user?.created_at
                  ? new Date(user.created_at).toLocaleDateString('zh-CN')
                  : '—'}
              </p>
            </div>
            <div>
              <label className="block text-xs text-ink-muted mb-1">登录方式</label>
              <p className="text-ink-text">
                {user?.oauth_provider === 'wechat' ? '微信' : '邮箱密码'}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-ink-light border border-ink-border rounded-xl p-6">
          <div className="flex items-center gap-3 mb-6">
            <CreditCard size={20} className="text-gold" />
            <h2 className="font-display text-lg text-gold">配额与订阅</h2>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 size={24} className="animate-spin text-gold" />
            </div>
          ) : (
            <div className="space-y-4">
              <div>
                <label className="block text-xs text-ink-muted mb-1">当前计划</label>
                <div className="flex items-center gap-2">
                  <Crown size={16} className="text-gold" />
                  <span className="text-ink-text font-display">
                    {planLabels[quota?.plan || 'free'] || quota?.plan || '免费版'}
                  </span>
                </div>
              </div>

              <div>
                <label className="block text-xs text-ink-muted mb-1">剩余次数</label>
                <div className="flex items-center gap-3">
                  <div className="flex-1 h-2 bg-ink rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-gold to-gold-light rounded-full transition-all"
                      style={{
                        width: quota
                          ? `${Math.max(0, (quota.remaining / Math.max(quota.total, 1)) * 100)}%`
                          : '0%',
                      }}
                    />
                  </div>
                  <span className="text-sm text-ink-muted">
                    {quota?.remaining ?? '—'} / {quota?.total ?? '—'}
                  </span>
                </div>
              </div>

              {subscription && (
                <div>
                  <label className="block text-xs text-ink-muted mb-1">订阅状态</label>
                  <p className="text-ink-text">
                    {subscription.status === 'active' ? '有效' : subscription.status}
                    {subscription.expires_at && (
                      <span className="text-ink-muted ml-2">
                        到期：{new Date(subscription.expires_at).toLocaleDateString('zh-CN')}
                      </span>
                    )}
                  </p>
                </div>
              )}

              <div className="pt-4 border-t border-ink-border">
                <button className="w-full py-2.5 bg-gold/20 text-gold rounded-lg text-sm font-medium hover:bg-gold/30 transition-all">
                  升级订阅
                </button>
              </div>
            </div>
          )}
        </div>

        <div className="lg:col-span-2 bg-ink-light border border-ink-border rounded-xl p-6">
          <div className="flex items-center gap-3 mb-6">
            <Shield size={20} className="text-gold" />
            <h2 className="font-display text-lg text-gold">修改密码</h2>
          </div>

          {passwordMsg && (
            <div className={`mb-4 p-3 rounded-lg text-sm ${
              passwordMsg.includes('失败') || passwordMsg.includes('不一致') || passwordMsg.includes('至少')
                ? 'bg-vermilion/10 border border-vermilion/30 text-vermilion'
                : 'bg-gold/10 border border-gold/30 text-gold'
            }`}>
              {passwordMsg}
            </div>
          )}

          <form onSubmit={handleChangePassword} className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            <div>
              <label className="block text-xs text-ink-muted mb-1.5">当前密码</label>
              <input
                type="password"
                value={oldPassword}
                onChange={(e) => setOldPassword(e.target.value)}
                required
                className="w-full px-3 py-2.5 bg-ink border border-ink-border rounded-lg text-ink-text text-sm focus:outline-none focus:border-gold/50 focus:ring-1 focus:ring-gold/20 transition-all"
                placeholder="输入当前密码"
              />
            </div>
            <div>
              <label className="block text-xs text-ink-muted mb-1.5">新密码</label>
              <input
                type="password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                required
                minLength={6}
                className="w-full px-3 py-2.5 bg-ink border border-ink-border rounded-lg text-ink-text text-sm focus:outline-none focus:border-gold/50 focus:ring-1 focus:ring-gold/20 transition-all"
                placeholder="至少6位"
              />
            </div>
            <div>
              <label className="block text-xs text-ink-muted mb-1.5">确认新密码</label>
              <div className="flex gap-2">
                <input
                  type="password"
                  value={confirmNewPassword}
                  onChange={(e) => setConfirmNewPassword(e.target.value)}
                  required
                  className="flex-1 px-3 py-2.5 bg-ink border border-ink-border rounded-lg text-ink-text text-sm focus:outline-none focus:border-gold/50 focus:ring-1 focus:ring-gold/20 transition-all"
                  placeholder="再次输入"
                />
                <button
                  type="submit"
                  disabled={changingPassword}
                  className="px-4 py-2.5 bg-vermilion hover:bg-vermilion-dark text-rice rounded-lg text-sm transition-all disabled:opacity-50 shrink-0"
                >
                  {changingPassword ? '修改中...' : '修改'}
                </button>
              </div>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
