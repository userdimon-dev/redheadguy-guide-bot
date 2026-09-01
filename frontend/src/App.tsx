import React, { useState, useEffect } from 'react';
import {
  Server,
  FolderPlus,
  FileText,
  Users,
  EyeOff,
  Plus,
  Trash2,
  Edit3,
  ArrowLeft,
  LogOut,
  LogIn,
  Terminal,
  Link as LinkIcon,
  Save,
  Moon,
  Sun
} from 'lucide-react';

declare global {
  interface Window {
    Telegram?: {
      WebApp?: {
        initData?: string;
      };
    };
    onTelegramAuth?: (user: unknown) => void;
  }
}

interface Category {
  id: string;
  title: string;
  is_hidden: boolean;
  sort_order: number;
  row_number: number;
  guide_count: number;
}

interface GuideItem {
  orig_idx: number;
  title: string;
  text: string;
  url?: string;
  url_label?: string;
  show_bot_links?: boolean;
  photo?: string;
  is_hidden: boolean;
  sort_order: number;
  row_number: number;
}

interface CategoryDetail {
  id: string;
  title: string;
  is_hidden: boolean;
  sort_order: number;
  row_number: number;
  guides: GuideItem[];
}

interface DashboardStats {
  categories: number;
  guides: number;
  users: number;
}

export function App() {
  const [siteConfig, setSiteConfig] = useState<{ site_name: string; bot_username: string; is_admin: boolean; user_id: number | null }>({ site_name: 'RedheadGuy Admin', bot_username: '', is_admin: false, user_id: null });
  const [view, setView] = useState<'dashboard' | 'category' | 'guide_view' | 'guide_edit' | 'login'>('dashboard');
  const [selectedCatId, setSelectedCatId] = useState<string | null>(null);
  const [selectedGuideIdx, setSelectedGuideIdx] = useState<number | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [categoryDetail, setCategoryDetail] = useState<CategoryDetail | null>(null);
  const [stats, setStats] = useState<DashboardStats>({ categories: 0, guides: 0, users: 0 });
  const [recentLogs, setRecentLogs] = useState<string[]>([]);

  // Theme state
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');

  // New / Edit Category Form state
  const [newCatId, setNewCatId] = useState('');
  const [newCatTitle, setNewCatTitle] = useState('');
  const [newCatRow, setNewCatRow] = useState(1);
  const [newCatSort, setNewCatSort] = useState(0);
  const [newCatHidden, setNewCatHidden] = useState(false);
  const [editingCatId, setEditingCatId] = useState<string | null>(null);

  // Render Telegram Widget dynamically on login view
  useEffect(() => {
    if (view === 'login' && siteConfig.bot_username) {
      window.onTelegramAuth = (user: unknown) => {
        fetch('/api/auth/telegram-widget', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(user)
        })
        .then(res => res.json())
        .then(data => {
          if (data.ok) {
            setSiteConfig(prev => ({ ...prev, is_admin: true, user_id: data.user.id }));
            setView('dashboard');
          } else {
            alert('Не удалось авторизоваться: вы не являетесь администратором');
          }
        });
      };

      const container = document.getElementById('telegram-widget-container');
      if (container) {
        container.innerHTML = '';
        const script = document.createElement('script');
        script.src = 'https://telegram.org/js/telegram-widget.js?22';
        script.setAttribute('data-telegram-login', siteConfig.bot_username);
        script.setAttribute('data-size', 'large');
        script.setAttribute('data-onauth', 'onTelegramAuth(user)');
        script.setAttribute('data-request-access', 'write');
        script.async = true;
        container.appendChild(script);
      }
    }
  }, [view, siteConfig.bot_username]);

  // Guide Edit Form state
  const [editGuideTitle, setEditGuideTitle] = useState('');
  const [editGuideText, setEditGuideText] = useState('');
  const [editGuideUrl, setEditGuideUrl] = useState('');
  const [editGuideUrlLabel, setEditGuideUrlLabel] = useState('');
  const [editGuideShowBotLinks, setEditGuideShowBotLinks] = useState(false);
  const [editGuideHidden, setEditGuideHidden] = useState(false);
  const [editGuideRow, setEditGuideRow] = useState(1);
  const [editGuideSort, setEditGuideSort] = useState(0);
  const [editGuidePhotoFile, setEditGuidePhotoFile] = useState<File | null>(null);
  const [editGuidePhotoRemove, setEditGuidePhotoRemove] = useState(false);

  // Load config & Telegram WebApp auto-auth
  useEffect(() => {
    fetch('/api/config')
      .then(res => res.json())
      .then(data => {
        setSiteConfig(data);
      });

    // Auto-auth via Telegram Mini App initData
    if (window.Telegram?.WebApp?.initData) {
      fetch('/api/auth/telegram-webapp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ initData: window.Telegram.WebApp.initData })
      })
      .then(res => res.json())
      .then(resData => {
        if (resData.ok) {
          setSiteConfig(prev => ({ ...prev, is_admin: true, user_id: resData.user.id }));
        }
      })
      .catch(() => {});
    }
  }, []);

  // Fetch Dashboard Stats & Categories
  const loadDashboardData = () => {
    fetch('/api/stats/dashboard')
      .then(res => res.json())
      .then(data => {
        setStats(data.stats);
        if (data.recent_logs) setRecentLogs(data.recent_logs);
      });

    fetch('/api/categories')
      .then(res => res.json())
      .then(data => {
        setCategories(data.categories || []);
      });
  };

  useEffect(() => {
    loadDashboardData();
  }, [view]);

  // Load Category Detail
  const loadCategory = (catId: string) => {
    fetch(`/api/category/${catId}`)
      .then(res => res.json())
      .then(data => {
        setCategoryDetail(data);
      });
  };

  useEffect(() => {
    if (selectedCatId && (view === 'category' || view === 'guide_edit' || view === 'guide_view')) {
      loadCategory(selectedCatId);
    }
  }, [selectedCatId, view]);

  // Handle Add Category
  const handleAddCategory = (e: React.FormEvent) => {
    e.preventDefault();
    fetch('/api/categories', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        id: newCatId,
        title: newCatTitle,
        row_number: newCatRow,
        sort_order: newCatSort,
        is_hidden: newCatHidden
      })
    })
    .then(res => res.json())
    .then(data => {
      if (data.ok) {
        setNewCatId('');
        setNewCatTitle('');
        loadDashboardData();
      } else {
        alert(data.error || 'Failed to create category');
      }
    });
  };

  // Handle Delete Category
  const handleDeleteCategory = (catId: string) => {
    if (!confirm('Delete category and all its guides?')) return;
    fetch(`/api/categories/${catId}/delete`, { method: 'POST' })
      .then(res => res.json())
      .then(() => loadDashboardData());
  };

  // Open Guide Editor
  const openGuideEditor = (catId: string, guideItem?: GuideItem, index?: number) => {
    setSelectedCatId(catId);
    setSelectedGuideIdx(index ?? null);
    if (guideItem) {
      setEditGuideTitle(guideItem.title);
      setEditGuideText(guideItem.text);
      setEditGuideUrl(guideItem.url || '');
      setEditGuideUrlLabel(guideItem.url_label || '');
      setEditGuideShowBotLinks(guideItem.show_bot_links || false);
      setEditGuideHidden(guideItem.is_hidden || false);
      setEditGuideRow(guideItem.row_number || 1);
      setEditGuideSort(guideItem.sort_order || 0);
    } else {
      setEditGuideTitle('');
      setEditGuideText('');
      setEditGuideUrl('');
      setEditGuideUrlLabel('');
      setEditGuideShowBotLinks(false);
      setEditGuideHidden(false);
      setEditGuideRow(1);
      setEditGuideSort(0);
    }
    setEditGuidePhotoFile(null);
    setEditGuidePhotoRemove(false);
    setView('guide_edit');
  };

  // Save Guide
  const handleSaveGuide = (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCatId) return;

    const formData = new FormData();
    formData.append('index', selectedGuideIdx !== null ? String(selectedGuideIdx) : 'new');
    formData.append('title', editGuideTitle);
    formData.append('text', editGuideText);
    formData.append('url', editGuideUrl);
    formData.append('url_label', editGuideUrlLabel);
    if (editGuideShowBotLinks) formData.append('show_bot_links', 'true');
    if (editGuideHidden) formData.append('is_hidden', 'true');
    formData.append('sort_order', String(editGuideSort));
    formData.append('row_number', String(editGuideRow));
    if (editGuidePhotoRemove) formData.append('photo_remove', '1');
    if (editGuidePhotoFile) formData.append('photo', editGuidePhotoFile);

    fetch(`/api/guides/${selectedCatId}/save`, {
      method: 'POST',
      body: formData,
    })
    .then(res => res.json())
    .then(data => {
      if (data.ok) {
        setView('category');
      } else {
        alert(data.error || 'Failed to save guide');
      }
    });
  };

  // Delete Guide
  const handleDeleteGuide = (catId: string, origIdx: number) => {
    if (!confirm('Delete this guide?')) return;
    fetch(`/api/guides/${catId}/${origIdx}/delete`, { method: 'POST' })
      .then(res => res.json())
      .then(() => {
        if (selectedCatId) loadCategory(selectedCatId);
      });
  };

  // Group Categories by Row
  const categoryRows = categories.reduce((acc, cat) => {
    const r = cat.row_number || 1;
    if (!acc[r]) acc[r] = [];
    acc[r].push(cat);
    return acc;
  }, {} as Record<number, Category[]>);

  // Group Guides by Row
  const guideRows = (categoryDetail?.guides || []).reduce((acc, g) => {
    const r = g.row_number || 1;
    if (!acc[r]) acc[r] = [];
    acc[r].push(g);
    return acc;
  }, {} as Record<number, GuideItem[]>);

  return (
    <div className={`min-h-screen ${theme === 'dark' ? 'bg-[#121417] text-slate-100' : 'bg-slate-50 text-slate-900'} font-sans antialiased transition-colors duration-200`}>
      {/* Top Navigation Bar */}
      <header className="border-b border-[#2A2E35] bg-[#1A1D21]/80 backdrop-blur sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
          <div
            onClick={() => setView('dashboard')}
            className="flex items-center gap-3 cursor-pointer group"
          >
            <div className="w-9 h-9 rounded-lg bg-[#FF5500]/10 border border-[#FF5500]/30 flex items-center justify-center text-[#FF5500] group-hover:scale-105 transition-transform">
              <Server className="w-5 h-5" />
            </div>
            <div>
              <div className="font-bold text-base tracking-wide flex items-center gap-2">
                {siteConfig.site_name}
                <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-[#FF5500]/20 text-[#FF5500]">SPA</span>
              </div>
              <div className="text-xs text-slate-400">Панель управления гайдами</div>
            </div>
          </div>

          <div className="flex items-center gap-3">
            <button
              onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
              className="p-2 rounded-lg border border-[#2A2E35] hover:bg-slate-800/50 text-slate-400 hover:text-slate-200 transition-colors"
              title="Toggle Theme"
            >
              {theme === 'dark' ? <Sun className="w-4 h-4 text-amber-400" /> : <Moon className="w-4 h-4 text-slate-600" />}
            </button>

            {siteConfig.is_admin ? (
              <div className="flex items-center gap-3">
                <span className="text-xs font-mono px-2.5 py-1 rounded-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse" />
                  Admin ID: {siteConfig.user_id}
                </span>
                <button
                  onClick={() => {
                    fetch('/api/auth/logout', { method: 'POST' }).then(() => {
                      setSiteConfig(prev => ({ ...prev, is_admin: false }));
                    });
                  }}
                  className="p-2 rounded-lg border border-red-500/30 bg-red-500/10 hover:bg-red-500/20 text-red-400 transition-colors"
                  title="Logout"
                >
                  <LogOut className="w-4 h-4" />
                </button>
              </div>
            ) : (
              <button
                onClick={() => setView('login')}
                className="px-3 py-1.5 rounded-lg bg-[#FF5500] hover:bg-[#E04B00] text-white text-xs font-medium flex items-center gap-1.5 transition-colors"
              >
                <LogIn className="w-3.5 h-3.5" />
                Логин
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Main Content Area */}
      <main className="max-w-6xl mx-auto px-4 py-8">
        {/* VIEW: Login */}
        {view === 'login' && (
          <div className="max-w-md mx-auto bg-[#1A1D21] border border-[#2A2E35] p-6 rounded-xl space-y-6 text-center">
            <h2 className="text-xl font-bold text-slate-100 flex items-center justify-center gap-2">
              <LogIn className="w-5 h-5 text-[#FF5500]" />
              Вход для администратора
            </h2>
            <p className="text-xs text-slate-400">
              Войдите с помощью виджета Telegram авторизации или откройте панель в Telegram Mini App.
            </p>

            <div className="py-4 flex justify-center bg-[#121417] p-4 rounded-xl border border-[#2A2E35]">
              <div id="telegram-widget-container">
                <p className="text-xs text-slate-400">
                  Загрузка виджета входа Telegram...
                </p>
              </div>
            </div>

            <button
              onClick={() => setView('dashboard')}
              className="text-xs text-slate-400 hover:text-slate-200"
            >
              ← Вернуться на главную
            </button>
          </div>
        )}

        {/* VIEW: Dashboard */}
        {view === 'dashboard' && (
          <div className="space-y-8">
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-[#1A1D21] border border-[#2A2E35] p-5 rounded-xl flex items-center gap-4">
                <div className="p-3 rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20">
                  <FolderPlus className="w-6 h-6" />
                </div>
                <div>
                  <div className="text-2xl font-extrabold text-slate-100">{stats.categories}</div>
                  <div className="text-xs text-slate-400">Всего категорий</div>
                </div>
              </div>

              <div className="bg-[#1A1D21] border border-[#2A2E35] p-5 rounded-xl flex items-center gap-4">
                <div className="p-3 rounded-lg bg-[#FF5500]/10 text-[#FF5500] border border-[#FF5500]/20">
                  <FileText className="w-6 h-6" />
                </div>
                <div>
                  <div className="text-2xl font-extrabold text-slate-100">{stats.guides}</div>
                  <div className="text-xs text-slate-400">Опубликовано гайдов</div>
                </div>
              </div>

              <div className="bg-[#1A1D21] border border-[#2A2E35] p-5 rounded-xl flex items-center gap-4">
                <div className="p-3 rounded-lg bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                  <Users className="w-6 h-6" />
                </div>
                <div>
                  <div className="text-2xl font-extrabold text-slate-100">{stats.users}</div>
                  <div className="text-xs text-slate-400">Пользователей бота</div>
                </div>
              </div>
            </div>

            {/* Admin Add Category Form */}
            {siteConfig.is_admin && (
              <div className="bg-[#1A1D21] border border-[#2A2E35] p-5 rounded-xl space-y-4">
                <div className="text-sm font-bold text-slate-200 flex items-center gap-2">
                  <Plus className="w-4 h-4 text-[#FF5500]" />
                  Добавить новую категорию
                </div>
                <form onSubmit={handleAddCategory} className="grid grid-cols-1 md:grid-cols-6 gap-3">
                  <input
                    type="text"
                    placeholder="id (напр. windows)"
                    value={newCatId}
                    onChange={e => setNewCatId(e.target.value)}
                    required
                    className="bg-[#121417] border border-[#2A2E35] text-sm rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-[#FF5500]"
                  />
                  <input
                    type="text"
                    placeholder="Название (🖥️ Настройка Windows)"
                    value={newCatTitle}
                    onChange={e => setNewCatTitle(e.target.value)}
                    required
                    className="md:col-span-2 bg-[#121417] border border-[#2A2E35] text-sm rounded-lg px-3 py-2 text-slate-200 focus:outline-none focus:border-[#FF5500]"
                  />
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-400">Ряд:</span>
                    <input
                      type="number"
                      value={newCatRow}
                      onChange={e => setNewCatRow(Number(e.target.value))}
                      min={1}
                      className="w-full bg-[#121417] border border-[#2A2E35] text-sm rounded-lg px-2 py-2 text-slate-200 focus:outline-none focus:border-[#FF5500]"
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs text-slate-400">Пор:</span>
                    <input
                      type="number"
                      value={newCatSort}
                      onChange={e => setNewCatSort(Number(e.target.value))}
                      className="w-full bg-[#121417] border border-[#2A2E35] text-sm rounded-lg px-2 py-2 text-slate-200 focus:outline-none focus:border-[#FF5500]"
                    />
                  </div>
                  <div className="flex items-center gap-2">
                    <label className="flex items-center gap-1.5 text-xs text-slate-300 cursor-pointer">
                      <input
                        type="checkbox"
                        checked={newCatHidden}
                        onChange={e => setNewCatHidden(e.target.checked)}
                        className="accent-[#FF5500]"
                      />
                      Скрыть
                    </label>
                  </div>
                  <button
                    type="submit"
                    className="bg-[#FF5500] hover:bg-[#E04B00] text-white font-medium text-sm rounded-lg px-4 py-2 transition-colors flex items-center justify-center gap-1.5"
                  >
                    <Plus className="w-4 h-4" /> Добавить
                  </button>
                </form>
              </div>
            )}

            {/* Edit Category Modal */}
            {editingCatId && (
              <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
                <div className="bg-[#1A1D21] border border-[#2A2E35] p-6 rounded-xl max-w-md w-full space-y-4">
                  <div className="text-lg font-bold text-slate-100 flex items-center justify-between">
                    <span>Редактирование категории <code className="text-[#FF5500]">{editingCatId}</code></span>
                    <button onClick={() => setEditingCatId(null)} className="text-slate-400 hover:text-slate-200">✕</button>
                  </div>

                  <form
                    onSubmit={e => {
                      e.preventDefault();
                      fetch(`/api/categories/${editingCatId}/rename`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                          title: newCatTitle,
                          row_number: newCatRow,
                          sort_order: newCatSort,
                          is_hidden: newCatHidden
                        })
                      })
                      .then(res => res.json())
                      .then(() => {
                        setEditingCatId(null);
                        loadDashboardData();
                      });
                    }}
                    className="space-y-3"
                  >
                    <div>
                      <label className="text-xs text-slate-300">Название</label>
                      <input
                        type="text"
                        value={newCatTitle}
                        onChange={e => setNewCatTitle(e.target.value)}
                        required
                        className="w-full bg-[#121417] border border-[#2A2E35] text-sm rounded-lg px-3 py-2 text-slate-100 mt-1"
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <label className="text-xs text-slate-300">Номер ряда</label>
                        <input
                          type="number"
                          value={newCatRow}
                          onChange={e => setNewCatRow(Number(e.target.value))}
                          min={1}
                          className="w-full bg-[#121417] border border-[#2A2E35] text-sm rounded-lg px-3 py-2 text-slate-100 mt-1"
                        />
                      </div>
                      <div>
                        <label className="text-xs text-slate-300">Порядок сортировки</label>
                        <input
                          type="number"
                          value={newCatSort}
                          onChange={e => setNewCatSort(Number(e.target.value))}
                          className="w-full bg-[#121417] border border-[#2A2E35] text-sm rounded-lg px-3 py-2 text-slate-100 mt-1"
                        />
                      </div>
                    </div>
                    <label className="flex items-center gap-2 text-xs text-red-400 cursor-pointer pt-1">
                      <input
                        type="checkbox"
                        checked={newCatHidden}
                        onChange={e => setNewCatHidden(e.target.checked)}
                        className="accent-red-500"
                      />
                      Скрыть категорию от пользователей
                    </label>

                    <div className="flex gap-2 pt-2">
                      <button
                        type="submit"
                        className="flex-1 bg-[#FF5500] hover:bg-[#E04B00] text-white font-medium text-sm py-2 rounded-lg transition-colors"
                      >
                        Сохранить изменения
                      </button>
                      <button
                        type="button"
                        onClick={() => setEditingCatId(null)}
                        className="px-4 bg-[#2A2E35] hover:bg-slate-700 text-slate-200 font-medium text-sm py-2 rounded-lg transition-colors"
                      >
                        Отмена
                      </button>
                    </div>
                  </form>
                </div>
              </div>
            )}

            {/* Category Rows List */}
            <div className="space-y-6">
              <div className="text-lg font-bold text-slate-100 flex items-center justify-between">
                <span>Сетка категорий</span>
                <span className="text-xs text-slate-400 font-normal">Сгруппировано по рядам</span>
              </div>

              {Object.keys(categoryRows).length === 0 ? (
                <div className="text-center py-12 text-slate-500 bg-[#1A1D21] border border-[#2A2E35] rounded-xl">
                  Категории не найдены.
                </div>
              ) : (
                Object.keys(categoryRows).sort((a, b) => Number(a) - Number(b)).map(rowNum => (
                  <div key={rowNum} className="bg-[#1A1D21] border border-[#2A2E35] rounded-xl p-4 space-y-3">
                    <div className="text-xs font-bold text-[#FF5500] uppercase tracking-wider">
                      Ряд {rowNum}
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                      {categoryRows[Number(rowNum)].map(cat => (
                        <div
                          key={cat.id}
                          className="group relative bg-[#121417] border border-[#2A2E35] hover:border-[#FF5500]/50 p-4 rounded-lg flex items-center justify-between gap-3 transition-colors"
                        >
                          <div
                            onClick={() => {
                              setSelectedCatId(cat.id);
                              setView('category');
                            }}
                            className="cursor-pointer flex-1 flex items-center gap-2.5"
                          >
                            <span className="font-semibold text-slate-200 group-hover:text-[#FF5500] transition-colors">
                              {cat.title}
                            </span>
                            <span className="text-[11px] px-2 py-0.5 rounded-full bg-[#2A2E35] text-slate-300 font-mono">
                              {cat.guide_count}
                            </span>
                            {cat.is_hidden && (
                              <span className="text-[10px] px-1.5 py-0.5 rounded bg-red-500/20 text-red-400 border border-red-500/30 flex items-center gap-1">
                                <EyeOff className="w-3 h-3" /> Скрыт
                              </span>
                            )}
                          </div>

                          {siteConfig.is_admin && (
                            <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                              <button
                                onClick={() => {
                                  setEditingCatId(cat.id);
                                  setNewCatTitle(cat.title);
                                  setNewCatRow(cat.row_number || 1);
                                  setNewCatSort(cat.sort_order || 0);
                                  setNewCatHidden(cat.is_hidden || false);
                                }}
                                className="p-1.5 rounded text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
                                title="Редактировать категорию"
                              >
                                <Edit3 className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handleDeleteCategory(cat.id)}
                                className="p-1.5 rounded text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                                title="Удалить категорию"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* Analytics Recent Logs */}
            {siteConfig.is_admin && recentLogs.length > 0 && (
              <div className="bg-[#1A1D21] border border-[#2A2E35] p-5 rounded-xl space-y-3">
                <div className="text-sm font-bold text-slate-200 flex items-center gap-2">
                  <Terminal className="w-4 h-4 text-emerald-400" />
                  Последняя активность пользователей (Аналитика)
                </div>
                <div className="bg-[#121417] p-3 rounded-lg font-mono text-xs text-slate-300 max-h-48 overflow-y-auto space-y-1">
                  {recentLogs.map((logLine, i) => (
                    <div key={i} className="whitespace-pre-wrap hover:bg-slate-800/40 px-1 py-0.5 rounded">
                      {logLine}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* VIEW: Category Detail */}
        {view === 'category' && categoryDetail && (
          <div className="space-y-6">
            <div className="flex items-center justify-between">
              <button
                onClick={() => setView('dashboard')}
                className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1.5 transition-colors"
              >
                <ArrowLeft className="w-4 h-4" /> ← Вернуться на главную
              </button>

              {siteConfig.is_admin && (
                <button
                  onClick={() => openGuideEditor(categoryDetail.id)}
                  className="bg-[#FF5500] hover:bg-[#E04B00] text-white text-xs font-medium px-3 py-2 rounded-lg flex items-center gap-1.5 transition-colors"
                >
                  <Plus className="w-4 h-4" /> Добавить гайд
                </button>
              )}
            </div>

            <div className="bg-[#1A1D21] border border-[#2A2E35] p-6 rounded-xl space-y-2">
              <h1 className="text-2xl font-extrabold text-slate-100 flex items-center gap-3">
                {categoryDetail.title}
                {categoryDetail.is_hidden && (
                  <span className="text-xs px-2 py-0.5 rounded bg-red-500/20 text-red-400 border border-red-500/30">
                    Скрытая категория
                  </span>
                )}
              </h1>
              <div className="text-xs text-slate-400">ID: <code className="text-[#FF5500]">{categoryDetail.id}</code></div>
            </div>

            {/* Guides Grouped by Row */}
            <div className="space-y-6">
              {Object.keys(guideRows).length === 0 ? (
                <div className="text-center py-12 text-slate-500 bg-[#1A1D21] border border-[#2A2E35] rounded-xl">
                  В этой категории пока нет гайдов.
                </div>
              ) : (
                Object.keys(guideRows).sort((a, b) => Number(a) - Number(b)).map(rowNum => (
                  <div key={rowNum} className="bg-[#1A1D21] border border-[#2A2E35] rounded-xl p-4 space-y-3">
                    <div className="text-xs font-bold text-[#FF5500] uppercase tracking-wider">
                      Ряд {rowNum}
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                      {guideRows[Number(rowNum)].map(guide => (
                        <div
                          key={guide.orig_idx}
                          className="bg-[#121417] border border-[#2A2E35] hover:border-slate-600 p-4 rounded-lg flex items-center justify-between gap-3"
                        >
                          <div
                            onClick={() => {
                              setSelectedGuideIdx(guide.orig_idx);
                              setView('guide_view');
                            }}
                            className="cursor-pointer flex-1 space-y-1"
                          >
                            <div className="font-semibold text-slate-200 hover:text-[#FF5500] transition-colors flex items-center gap-2">
                              {guide.title}
                              {guide.is_hidden && (
                                <span className="text-[10px] px-1.5 py-0.5 rounded bg-red-500/20 text-red-400 border border-red-500/30">
                                  Скрыт
                                </span>
                              )}
                            </div>
                            {guide.url && (
                              <div className="text-xs text-blue-400 flex items-center gap-1">
                                <LinkIcon className="w-3 h-3" /> {guide.url_label || guide.url}
                              </div>
                            )}
                          </div>

                          {siteConfig.is_admin && (
                            <div className="flex items-center gap-2">
                              <button
                                onClick={() => openGuideEditor(categoryDetail.id, guide, guide.orig_idx)}
                                className="p-1.5 rounded text-slate-400 hover:text-slate-200 hover:bg-slate-800 transition-colors"
                                title="Редактировать гайд"
                              >
                                <Edit3 className="w-4 h-4" />
                              </button>
                              <button
                                onClick={() => handleDeleteGuide(categoryDetail.id, guide.orig_idx)}
                                className="p-1.5 rounded text-slate-400 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                                title="Удалить гайд"
                              >
                                <Trash2 className="w-4 h-4" />
                              </button>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        )}

        {/* VIEW: Guide View / Telegram Mini App Preview */}
        {view === 'guide_view' && selectedCatId && selectedGuideIdx !== null && (() => {
          const currentGuide = categoryDetail?.guides.find(g => g.orig_idx === selectedGuideIdx);
          return (
            <div className="space-y-6">
              <button
                onClick={() => setView('category')}
                className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1.5 transition-colors"
              >
                <ArrowLeft className="w-4 h-4" /> ← Вернуться к категории
              </button>

              {/* Telegram Card Component */}
              <div className="max-w-2xl mx-auto bg-[#18222D] border border-[#232E3C] rounded-2xl overflow-hidden shadow-2xl space-y-4 p-5">
                {currentGuide?.photo && (
                  <div className="rounded-xl overflow-hidden max-h-80 border border-[#232E3C]">
                    <img
                      src={`/${currentGuide.photo}`}
                      alt="Фото гайда"
                      className="w-full h-full object-cover"
                    />
                  </div>
                )}

                <div className="text-xl font-bold text-white">
                  {currentGuide?.title}
                </div>

                <div
                  className="text-sm text-slate-200 leading-relaxed space-y-2"
                  dangerouslySetInnerHTML={{ __html: currentGuide?.text || '' }}
                />

                {currentGuide?.url && (
                  <a
                    href={currentGuide.url}
                    target="_blank"
                    rel="noreferrer"
                    className="block w-full text-center bg-[#229ED9] hover:bg-[#1B86B9] text-white font-semibold text-sm py-2.5 rounded-xl transition-colors"
                  >
                    {currentGuide.url_label || '🔗 Открыть ссылку'}
                  </a>
                )}
              </div>
            </div>
          );
        })()}

        {/* VIEW: Guide Editor */}
        {view === 'guide_edit' && selectedCatId && (
          <div className="space-y-6">
            <button
              onClick={() => setView('category')}
              className="text-xs text-slate-400 hover:text-slate-200 flex items-center gap-1.5 transition-colors"
            >
              <ArrowLeft className="w-4 h-4" /> Отмена и назад
            </button>

            <form onSubmit={handleSaveGuide} className="bg-[#1A1D21] border border-[#2A2E35] p-6 rounded-xl space-y-6">
              <div className="text-lg font-bold text-slate-100">
                {selectedGuideIdx !== null ? 'Редактирование гайда' : 'Создание нового гайда'}
              </div>

              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-300">Заголовок</label>
                <input
                  type="text"
                  value={editGuideTitle}
                  onChange={e => setEditGuideTitle(e.target.value)}
                  required
                  placeholder="напр. 🖥️ Инструкция по настройке Windows"
                  className="w-full bg-[#121417] border border-[#2A2E35] rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-[#FF5500]"
                />
              </div>

              <div className="space-y-2">
                <label className="text-xs font-semibold text-slate-300">HTML Содержимое гайда</label>
                <textarea
                  value={editGuideText}
                  onChange={e => setEditGuideText(e.target.value)}
                  required
                  rows={8}
                  placeholder="Инструкция в формате HTML..."
                  className="w-full bg-[#121417] border border-[#2A2E35] rounded-lg p-3 text-sm font-mono text-slate-200 focus:outline-none focus:border-[#FF5500]"
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-300">URL кнопки (Опционально)</label>
                  <input
                    type="text"
                    value={editGuideUrl}
                    onChange={e => setEditGuideUrl(e.target.value)}
                    placeholder="https://example.com"
                    className="w-full bg-[#121417] border border-[#2A2E35] rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-[#FF5500]"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-300">Текст кнопки</label>
                  <input
                    type="text"
                    value={editGuideUrlLabel}
                    onChange={e => setEditGuideUrlLabel(e.target.value)}
                    placeholder="🔗 Открыть"
                    className="w-full bg-[#121417] border border-[#2A2E35] rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-[#FF5500]"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-300">Номер ряда</label>
                  <input
                    type="number"
                    value={editGuideRow}
                    onChange={e => setEditGuideRow(Number(e.target.value))}
                    min={1}
                    className="w-full bg-[#121417] border border-[#2A2E35] rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-[#FF5500]"
                  />
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-semibold text-slate-300">Порядок сортировки</label>
                  <input
                    type="number"
                    value={editGuideSort}
                    onChange={e => setEditGuideSort(Number(e.target.value))}
                    className="w-full bg-[#121417] border border-[#2A2E35] rounded-lg px-3 py-2 text-sm text-slate-100 focus:outline-none focus:border-[#FF5500]"
                  />
                </div>
              </div>

              {/* Photo Upload & Photo Removal Controls */}
              <div className="bg-[#121417] p-4 rounded-lg border border-[#2A2E35] space-y-3">
                <label className="text-xs font-semibold text-slate-300 block">
                  Изображение гайда (опционально)
                </label>

                {(() => {
                  const currG = categoryDetail?.guides.find(g => g.orig_idx === selectedGuideIdx);
                  if (currG?.photo && !editGuidePhotoRemove) {
                    return (
                      <div className="flex items-center gap-3 bg-[#1A1D21] p-2.5 rounded-lg border border-[#2A2E35]">
                        <img
                          src={`/${currG.photo}`}
                          alt="Текущее фото"
                          className="w-12 h-12 object-cover rounded"
                        />
                        <div className="flex-1 text-xs text-slate-300">
                          <div>Текущее фото: <span className="font-mono text-slate-400">{currG.photo}</span></div>
                        </div>
                        <label className="flex items-center gap-1.5 text-xs text-red-400 cursor-pointer font-medium">
                          <input
                            type="checkbox"
                            checked={editGuidePhotoRemove}
                            onChange={e => setEditGuidePhotoRemove(e.target.checked)}
                            className="accent-red-500"
                          />
                          Удалить фото
                        </label>
                      </div>
                    );
                  }
                  return null;
                })()}

                <input
                  type="file"
                  accept="image/*"
                  onChange={e => {
                    if (e.target.files && e.target.files[0]) {
                      setEditGuidePhotoFile(e.target.files[0]);
                      setEditGuidePhotoRemove(false);
                    } else {
                      setEditGuidePhotoFile(null);
                    }
                  }}
                  className="block w-full text-xs text-slate-400 file:mr-3 file:py-1.5 file:px-3 file:rounded-lg file:border-0 file:text-xs file:font-medium file:bg-[#FF5500] file:text-white hover:file:bg-[#E04B00] cursor-pointer"
                />
              </div>

              <div className="flex items-center gap-6">
                <label className="flex items-center gap-2 text-xs text-slate-300 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={editGuideShowBotLinks}
                    onChange={e => setEditGuideShowBotLinks(e.target.checked)}
                    className="accent-[#FF5500]"
                  />
                  Показывать основные кнопки бота
                </label>
                <label className="flex items-center gap-2 text-xs text-red-400 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={editGuideHidden}
                    onChange={e => setEditGuideHidden(e.target.checked)}
                    className="accent-red-500"
                  />
                  Скрыть гайд (Черновик)
                </label>
              </div>

              <button
                type="submit"
                className="bg-[#FF5500] hover:bg-[#E04B00] text-white font-medium text-sm px-5 py-2.5 rounded-lg transition-colors flex items-center gap-2"
              >
                <Save className="w-4 h-4" /> Сохранить гайд
              </button>
            </form>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
