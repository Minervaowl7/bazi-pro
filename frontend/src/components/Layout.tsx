import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { Compass, History, User, LogOut, Menu, X } from 'lucide-react';
import { useAuthStore } from '../store/authStore';
import { useState } from 'react';

const navItems = [
  { to: '/analyze', label: '命盘分析', icon: Compass },
  { to: '/history', label: '历史记录', icon: History },
  { to: '/account', label: '我的账户', icon: User },
];

export default function Layout() {
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  return (
    <div className="min-h-screen flex bg-ink">
      {sidebarOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-30 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      <aside
        className={`
          fixed lg:static inset-y-0 left-0 z-40 w-64 bg-ink-light border-r border-ink-border
          transform transition-transform duration-300 ease-in-out
          ${sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}
        `}
      >
        <div className="flex flex-col h-full">
          <div className="p-6 border-b border-ink-border">
            <h1 className="font-display text-2xl text-gold tracking-widest">
              八字命理
            </h1>
            <p className="text-ink-muted text-xs mt-1 tracking-wider">BAZI-PRO</p>
          </div>

          <nav className="flex-1 py-4">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                onClick={() => setSidebarOpen(false)}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-6 py-3 text-sm transition-all duration-200 ${
                    isActive
                      ? 'text-gold bg-ink-lighter border-r-2 border-gold'
                      : 'text-ink-muted hover:text-ink-text hover:bg-ink-lighter'
                  }`
                }
              >
                <item.icon size={18} />
                {item.label}
              </NavLink>
            ))}
          </nav>

          <div className="p-4 border-t border-ink-border">
            <div className="flex items-center gap-3 mb-3 px-2">
              <div className="w-8 h-8 rounded-full bg-vermilion/20 flex items-center justify-center text-vermilion text-sm font-display">
                {user?.display_name?.[0] || user?.email?.[0]?.toUpperCase() || '?'}
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm text-ink-text truncate">
                  {user?.display_name || user?.email || '未登录'}
                </p>
              </div>
            </div>
            <button
              onClick={handleLogout}
              className="flex items-center gap-2 px-2 py-2 text-sm text-ink-muted hover:text-vermilion transition-colors w-full"
            >
              <LogOut size={16} />
              退出登录
            </button>
          </div>
        </div>
      </aside>

      <div className="flex-1 flex flex-col min-w-0">
        <header className="lg:hidden flex items-center justify-between px-4 py-3 bg-ink-light border-b border-ink-border">
          <button
            onClick={() => setSidebarOpen(!sidebarOpen)}
            className="text-ink-muted hover:text-ink-text transition-colors"
          >
            {sidebarOpen ? <X size={24} /> : <Menu size={24} />}
          </button>
          <span className="font-display text-gold tracking-widest">八字命理</span>
          <div className="w-6" />
        </header>

        <main className="flex-1 overflow-y-auto">
          <div className="animate-fade-in">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  );
}
