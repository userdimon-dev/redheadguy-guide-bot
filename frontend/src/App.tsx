import React, { useState, useEffect } from 'react';
import {
  FolderPlus,
  FileText,
  Plus,
  Trash2,
  Save,
  Moon,
  Sun,
  ChevronUp,
  ChevronDown,
  ChevronRight,
  Smartphone,
  MessageSquare,
  Bold,
  Italic,
  Quote,
  Code,
  Tag as TagIcon,
  X,
  Check,
  Search,
  Lock,
  ExternalLink,
  Menu,
  Wrench,
  Eye
} from 'lucide-react';

interface InlineButton {
  text: string;
  type: 'miniapp' | 'callback' | 'url';
  payload: string;
}

interface InlineRow {
  row_number: number;
  buttons: InlineButton[];
}

interface GuideItem {
  orig_idx: number;
  title: string;
  slug?: string;
  summary?: string;
  text: string;
  content?: string;
  tags?: string[];
  buttons?: InlineRow[];
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

interface PublicCategory {
  id: string;
  title: string;
  guides: GuideItem[];
}

interface Category {
  id: string;
  title: string;
  is_hidden: boolean;
  sort_order: number;
  row_number: number;
  guide_count: number;
}

declare global {
  interface Window {
    Telegram?: {
      WebApp?: {
        initData?: string;
        ready?: () => void;
        expand?: () => void;
        openTelegramLink?: (url: string) => void;
        openLink?: (url: string) => void;
      };
    };
    onTelegramAuth?: (user: unknown) => void;
  }
}

// Convert HTML / Quill.js / Markdown content into clean, safe formatted HTML
function renderCleanHtmlContent(text: string = '') {
  if (!text) return { __html: '' };

  let html = text;

  // Clean Quill.js list helpers (<span class="ql-ui" contenteditable="false"></span>)
  html = html.replace(/<span\s+class="ql-ui"[^>]*>.*?<\/span>/gi, '');

  // Convert Quill <li data-list="bullet"> to <ul><li>
  html = html.replace(/<li\s+data-list="bullet"[^>]*>(.*?)<\/li>/gi, '<ul class="list-disc pl-5 my-1"><li>$1</li></ul>');
  html = html.replace(/<li\s+data-list="ordered"[^>]*>(.*?)<\/li>/gi, '<ol class="list-decimal pl-5 my-1"><li>$1</li></ol>');

  // If text is raw Markdown without HTML tags, apply basic Markdown rules
  if (!/<[a-z][\s\S]*>/i.test(html)) {
    html = html
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.*?)\*/g, '<em>$1</em>')
      .replace(/`([^`]+)`/g, '<code class="bg-[#121417] text-emerald-400 font-mono px-1.5 py-0.5 rounded border border-[#2A2E35]">$1</code>')
      .replace(/\n/g, '<br/>');
  }

  return { __html: html };
}

export function App() {
  const [siteConfig, setSiteConfig] = useState<{ site_name: string; bot_username: string; brand_name?: string; is_admin: boolean; user_id: number | null }>({
    site_name: 'RedheadGuy Admin Panel',
    bot_username: '',
    brand_name: 'REDHEADGUY PRIVATE',
    is_admin: false,
    user_id: null
  });

  const [isLoading, setIsLoading] = useState(true);
  const [isAdmin, setIsAdmin] = useState(false);
  const [activeViewMode, setActiveViewMode] = useState<'studio' | 'public'>('public');

  // Categories & Guides state
  const [categories, setCategories] = useState<Category[]>([]);
  const [publicCategories, setPublicCategories] = useState<PublicCategory[]>([]);
  const [activeCatId, setActiveCatId] = useState<string | null>(null);
  const [categoryDetail, setCategoryDetail] = useState<CategoryDetail | null>(null);
  const [activeGuideIdx, setActiveGuideIdx] = useState<number | null>(null);

  // Public Viewer State
  const [selectedPublicCategory, setSelectedPublicCategory] = useState<PublicCategory | null>(null);
  const [selectedPublicGuide, setSelectedPublicGuide] = useState<GuideItem | null>(null);
  const [expandedCategories, setExpandedCategories] = useState<Record<string, boolean>>({});
  const [searchQuery, setSearchQuery] = useState('');
  const [mobileDrawerOpen, setMobileDrawerOpen] = useState(false);

  // Theme & Preview Mode
  const [theme, setTheme] = useState<'dark' | 'light'>('dark');
  const [previewMode, setPreviewMode] = useState<'miniapp' | 'telegram'>('miniapp');

  // Auth Modal & Toast
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [autoSaved, setAutoSaved] = useState(true);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  // New Category Modal
  const [showCatModal, setShowCatModal] = useState(false);
  const [newCatId, setNewCatId] = useState('');
  const [newCatTitle, setNewCatTitle] = useState('');

  // Guide Form State (Admin Studio)
  const [guideTitle, setGuideTitle] = useState('');
  const [guideSlug, setGuideSlug] = useState('');
  const [guideSummary, setGuideSummary] = useState('');
  const [guideContent, setGuideContent] = useState('');
  const [guideTags, setGuideTags] = useState<string[]>([]);
  const [tagInput, setTagInput] = useState('');
  const [guideRows, setGuideRows] = useState<InlineRow[]>([
    { row_number: 1, buttons: [{ text: '🚀 Открыть сервис', type: 'miniapp', payload: 'https://t.me/bot' }] }
  ]);
  const [guideIsHidden, setGuideIsHidden] = useState(false);

  const isInsideTMA = Boolean(window.Telegram?.WebApp?.initData);

  const showToast = (msg: string) => {
    setToastMessage(msg);
    setTimeout(() => setToastMessage(null), 3000);
  };

  // App Initialization & Role Routing
  useEffect(() => {
    const tg = window.Telegram?.WebApp;
    if (tg) {
      if (tg.ready) tg.ready();
      if (tg.expand) tg.expand();
    }

    fetch('/api/config')
      .then(res => res.json())
      .then(data => {
        setSiteConfig(data);
        if (data.is_admin) {
          setIsAdmin(true);
          setActiveViewMode('studio');
        }
      });

    // Check Telegram Mini App initData
    if (tg?.initData) {
      fetch('/api/auth/telegram-webapp', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ initData: tg.initData })
      })
      .then(res => res.json())
      .then(resData => {
        if (resData.authenticated && resData.isAdmin) {
          setIsAdmin(true);
          setActiveViewMode('studio');
          setSiteConfig(prev => ({ ...prev, is_admin: true, user_id: resData.user?.id || null }));
        } else {
          setIsAdmin(false);
          setActiveViewMode('public');
        }
        setIsLoading(false);
      })
      .catch(() => setIsLoading(false));
    } else {
      setIsLoading(false);
    }

    loadCategories();
    loadPublicGuides();
  }, []);

  // Telegram Widget Login Modal Setup
  useEffect(() => {
    if (showLoginModal && siteConfig.bot_username) {
      window.onTelegramAuth = (user: unknown) => {
        fetch('/api/auth/telegram-widget', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(user)
        })
        .then(res => res.json())
        .then(data => {
          if (data.ok) {
            setIsAdmin(true);
            setActiveViewMode('studio');
            setSiteConfig(prev => ({ ...prev, is_admin: true, user_id: data.user_id }));
            setShowLoginModal(false);
            showToast('Авторизация выполнена! Доступны права администратора.');
          } else {
            alert('Не удалось войти: пользователь не является администратором бота');
          }
        });
      };

      const container = document.getElementById('modal-telegram-widget');
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
  }, [showLoginModal, siteConfig.bot_username]);

  const loadCategories = () => {
    fetch('/api/categories')
      .then(res => res.json())
      .then(data => {
        const cats = data.categories || [];
        setCategories(cats);
        if (cats.length > 0 && !activeCatId) {
          setActiveCatId(cats[0].id);
        }
      });
  };

  const loadPublicGuides = () => {
    fetch('/api/guides/public')
      .then(res => res.json())
      .then(data => {
        const pubCats: PublicCategory[] = data.categories || [];
        setPublicCategories(pubCats);

        const exp: Record<string, boolean> = {};
        pubCats.forEach(c => exp[c.id] = true);
        setExpandedCategories(exp);

        if (pubCats.length > 0) {
          setSelectedPublicCategory(pubCats[0]);
          if (pubCats[0].guides.length > 0) {
            setSelectedPublicGuide(pubCats[0].guides[0]);
          }
        }
      });
  };

  // Load Active Category for Admin Studio
  useEffect(() => {
    if (activeCatId && isAdmin) {
      fetch(`/api/category/${activeCatId}`)
        .then(res => res.json())
        .then(data => {
          setCategoryDetail(data);
          if (data.guides && data.guides.length > 0) {
            selectGuide(data.guides[0], 0);
          } else {
            resetGuideForm();
          }
        });
    }
  }, [activeCatId, isAdmin]);

  const selectGuide = (guide: GuideItem, idx: number) => {
    setActiveGuideIdx(guide.orig_idx !== undefined ? guide.orig_idx : idx);
    setGuideTitle(guide.title);
    setGuideSlug(guide.slug || `guide-${guide.orig_idx}`);
    setGuideSummary(guide.summary || guide.title);
    setGuideContent(guide.content || guide.text);
    setGuideTags(guide.tags || ['Инструкция', 'Гайд']);
    setGuideRows(guide.buttons && guide.buttons.length > 0 ? guide.buttons : [
      { row_number: 1, buttons: [{ text: '🚀 Открыть сервис', type: 'miniapp', payload: 'https://t.me/bot' }] }
    ]);
    setGuideIsHidden(guide.is_hidden || false);
    setAutoSaved(true);
  };

  const resetGuideForm = () => {
    setActiveGuideIdx(null);
    setGuideTitle('Новый гайд');
    setGuideSlug('new-guide');
    setGuideSummary('Краткое описание статьи для бота');
    setGuideContent('### Заголовок инструкции\n\nВведите форматированный **Markdown** текст.');
    setGuideTags(['Гайд']);
    setGuideRows([
      { row_number: 1, buttons: [{ text: '🔗 Ссылка', type: 'url', payload: 'https://example.com' }] }
    ]);
    setGuideIsHidden(false);
  };

  // Reorder Category
  const moveCategory = (index: number, direction: 'up' | 'down') => {
    const newCats = [...categories];
    const targetIdx = direction === 'up' ? index - 1 : index + 1;
    if (targetIdx < 0 || targetIdx >= newCats.length) return;

    const temp = newCats[index];
    newCats[index] = newCats[targetIdx];
    newCats[targetIdx] = temp;

    newCats.forEach((c, idx) => c.sort_order = idx);
    setCategories(newCats);

    // Persist new category order immediately
    fetch('/api/guides/reorder', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ categories: newCats.map((c, i) => ({ id: c.id, sort_order: i })) })
    })
    .then(res => res.json())
    .then(data => {
      if (data.ok) {
        showToast('Порядок категорий сохранен!');
        loadPublicGuides();
      }
    });
  };

  // Reorder Guide/Article within active category
  const moveGuide = (gIndex: number, direction: 'up' | 'down') => {
    if (!categoryDetail || !activeCatId) return;

    const currentGuides = [...categoryDetail.guides];
    const targetIdx = direction === 'up' ? gIndex - 1 : gIndex + 1;
    if (targetIdx < 0 || targetIdx >= currentGuides.length) return;

    const temp = currentGuides[gIndex];
    currentGuides[gIndex] = currentGuides[targetIdx];
    currentGuides[targetIdx] = temp;

    const orderIndices = currentGuides.map(g => g.orig_idx);

    fetch('/api/guides/reorder', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ category_id: activeCatId, order: orderIndices })
    })
    .then(res => res.json())
    .then(data => {
      if (data.ok) {
        showToast('Порядок статей обновлен');
        loadPublicGuides();
        fetch(`/api/category/${activeCatId}`)
          .then(res => res.json())
          .then(catData => setCategoryDetail(catData));
      }
    });
  };

  // Add Category
  const handleAddCategory = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newCatId || !newCatTitle) return;

    fetch('/api/categories', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ id: newCatId, title: newCatTitle, sort_order: categories.length })
    })
    .then(res => res.json())
    .then(data => {
      if (data.ok) {
        setShowCatModal(false);
        setNewCatId('');
        setNewCatTitle('');
        loadCategories();
        setActiveCatId(newCatId);
        showToast('Категория успешно создана!');
      } else {
        alert(data.error || 'Ошибка при создании категории');
      }
    });
  };

  // Save Guide
  const handleSaveGuide = (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!activeCatId) return;

    const formData = new FormData();
    formData.append('index', activeGuideIdx !== null ? String(activeGuideIdx) : 'new');
    formData.append('title', guideTitle);
    formData.append('slug', guideSlug);
    formData.append('summary', guideSummary);
    formData.append('text', guideContent);
    formData.append('content', guideContent);
    formData.append('tags', JSON.stringify(guideTags));
    formData.append('buttons', JSON.stringify(guideRows));
    if (guideIsHidden) formData.append('is_hidden', 'true');

    const currGuide = categoryDetail?.guides.find(g => g.orig_idx === activeGuideIdx);
    formData.append('sort_order', String(currGuide?.sort_order || 0));
    formData.append('row_number', String(currGuide?.row_number || 1));

    fetch(`/api/guides/${activeCatId}/save`, {
      method: 'POST',
      body: formData
    })
    .then(res => res.json())
    .then(data => {
      if (data.ok) {
        // Also persist full category order on publish
        fetch('/api/guides/reorder', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ categories: categories.map((c, i) => ({ id: c.id, sort_order: i })) })
        }).catch(() => {});

        setAutoSaved(true);
        showToast('Порядок разделов и статей успешно опубликован!');
        loadPublicGuides();
        fetch(`/api/category/${activeCatId}`)
          .then(res => res.json())
          .then(catData => setCategoryDetail(catData));
      }
    });
  };

  // Markdown format insertion
  const insertFormatting = (symbol: string, wrapper: boolean = true) => {
    if (wrapper) {
      setGuideContent(prev => `${prev}\n${symbol}Выделенный текст${symbol}\n`);
    } else {
      setGuideContent(prev => `${prev}\n${symbol} `);
    }
    setAutoSaved(false);
  };

  // Tag Handlers
  const handleAddTag = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && tagInput.trim()) {
      e.preventDefault();
      if (!guideTags.includes(tagInput.trim())) {
        setGuideTags([...guideTags, tagInput.trim()]);
      }
      setTagInput('');
      setAutoSaved(false);
    }
  };

  const removeTag = (tagToRemove: string) => {
    setGuideTags(guideTags.filter(t => t !== tagToRemove));
    setAutoSaved(false);
  };

  // Button Rows Handlers
  const addRow = () => {
    setGuideRows([...guideRows, { row_number: guideRows.length + 1, buttons: [] }]);
    setAutoSaved(false);
  };

  const addButtonToRow = (rowIndex: number) => {
    if (guideRows[rowIndex].buttons.length >= 3) {
      alert('Максимум 3 кнопки в одном ряду!');
      return;
    }
    const updated = [...guideRows];
    updated[rowIndex].buttons.push({
      text: 'Новая кнопка',
      type: 'url',
      payload: 'https://t.me/redheadguy'
    });
    setGuideRows(updated);
    setAutoSaved(false);
  };

  const updateButton = (rowIndex: number, btnIndex: number, field: keyof InlineButton, value: string) => {
    const updated = [...guideRows];
    updated[rowIndex].buttons[btnIndex][field] = value as any;
    setGuideRows(updated);
    setAutoSaved(false);
  };

  const removeButton = (rowIndex: number, btnIndex: number) => {
    const updated = [...guideRows];
    updated[rowIndex].buttons.splice(btnIndex, 1);
    setGuideRows(updated);
    setAutoSaved(false);
  };

  // Execute Public Button Action
  const handlePublicButtonClick = (btn: InlineButton) => {
    if (btn.type === 'url' || btn.type === 'miniapp') {
      if (window.Telegram?.WebApp?.openLink && btn.payload.startsWith('http')) {
        window.Telegram.WebApp.openLink(btn.payload);
      } else {
        window.open(btn.payload, '_blank');
      }
    } else if (btn.type === 'callback') {
      showToast(`Callback действие: ${btn.payload}`);
    }
  };

  const toggleCategoryExpand = (catId: string) => {
    setExpandedCategories(prev => ({ ...prev, [catId]: !prev[catId] }));
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#121417] text-slate-100 flex items-center justify-center font-sans">
        <div className="flex flex-col items-center gap-3">
          <div className="w-8 h-8 border-2 border-[#FF5500] border-t-transparent rounded-full animate-spin" />
          <span className="text-xs text-slate-400">Загрузка Базы Знаний...</span>
        </div>
      </div>
    );
  }

  return (
    <div className={`h-screen ${theme === 'dark' ? 'bg-[#121417] text-slate-100' : 'bg-slate-100 text-slate-900'} font-sans flex flex-col overflow-hidden antialiased`}>
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed top-4 right-4 z-50 bg-[#FF5500] text-white text-xs font-semibold px-4 py-2.5 rounded-lg shadow-xl flex items-center gap-2 animate-bounce">
          <Check className="w-4 h-4" />
          {toastMessage}
        </div>
      )}

      {/* Top Header Navigation (Fixed Height) */}
      <header className="border-b border-[#2A2E35] bg-[#1A1D21] px-3 md:px-6 py-2.5 flex items-center justify-between z-40 gap-2 shrink-0">
        <div className="flex items-center gap-2 min-w-0 flex-1">
          {activeViewMode === 'public' && (
            <button
              onClick={() => setMobileDrawerOpen(!mobileDrawerOpen)}
              className="md:hidden p-1.5 rounded-lg border border-[#2A2E35] bg-[#121417] text-slate-300 shrink-0"
            >
              <Menu className="w-4 h-4" />
            </button>
          )}

          <img src="/api/logo" alt="Logo" className="w-7 h-8 md:w-8 md:h-8 rounded-lg border border-[#2A2E35] object-cover shrink-0" />
          <div className="min-w-0 flex-1">
            <h1 className="font-extrabold text-xs md:text-sm tracking-wide text-white flex items-center gap-1.5 truncate">
              <span className="truncate">{siteConfig.brand_name || siteConfig.site_name}</span>
              <span className="text-[9px] uppercase font-mono px-1.5 py-0.5 rounded bg-[#FF5500]/20 text-[#FF5500] border border-[#FF5500]/30 shrink-0">v2.0</span>
            </h1>
            <p className="text-[10px] md:text-[11px] text-slate-400 truncate">
              {isAdmin && activeViewMode === 'studio' ? 'Редактор Базы Знаний' : 'База Знаний & Инструкции'}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2 shrink-0">
          {/* Mode Switcher for Admins [ 🛠️ Редактор / 👁️ Читалка ] */}
          {isAdmin && (
            <button
              onClick={() => setActiveViewMode(activeViewMode === 'studio' ? 'public' : 'studio')}
              className="bg-[#2A2E35] hover:bg-slate-700 text-slate-200 text-[11px] font-semibold px-2.5 py-1.5 rounded-lg transition-colors flex items-center gap-1 border border-[#3A3F47]"
              title="Переключить режим вида"
            >
              {activeViewMode === 'studio' ? (
                <>
                  <Eye className="w-3.5 h-3.5 text-[#FF5500]" />
                  <span className="hidden sm:inline">Читалка</span>
                </>
              ) : (
                <>
                  <Wrench className="w-3.5 h-3.5 text-[#FF5500]" />
                  <span className="hidden sm:inline">Редактор</span>
                </>
              )}
            </button>
          )}

          {isAdmin && activeViewMode === 'studio' ? (
            <>
              <div className="hidden lg:flex items-center gap-2 text-xs">
                <span className={`w-2 h-2 rounded-full ${autoSaved ? 'bg-emerald-400' : 'bg-amber-400 animate-ping'}`} />
                <span className="text-slate-400 font-mono text-[11px]">
                  {autoSaved ? 'Сохранено' : 'Есть правки'}
                </span>
              </div>

              <button
                onClick={() => handleSaveGuide()}
                className="bg-[#FF5500] hover:bg-[#E04B00] text-white text-[11px] md:text-xs font-semibold px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1 shadow-lg shadow-[#FF5500]/20"
              >
                <Save className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Опубликовать</span>
              </button>
            </>
          ) : (
            !isInsideTMA && (
              <button
                onClick={() => setShowLoginModal(true)}
                className="bg-[#2A2E35] hover:bg-slate-700 text-slate-200 text-[11px] font-semibold px-2.5 py-1.5 rounded-lg transition-colors flex items-center gap-1 border border-[#3A3F47]"
              >
                <Lock className="w-3.5 h-3.5 text-[#FF5500]" />
                <span className="hidden sm:inline">Вход</span>
              </button>
            )
          )}

          <button
            onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}
            className="p-1.5 md:p-2 rounded-lg border border-[#2A2E35] hover:bg-slate-800 text-slate-400 transition-colors"
          >
            {theme === 'dark' ? <Sun className="w-3.5 h-3.5 text-amber-400" /> : <Moon className="w-3.5 h-3.5 text-slate-600" />}
          </button>
        </div>
      </header>

      {/* RENDER MODE A: ADMIN STUDIO (isAdmin === true && activeViewMode === 'studio') */}
      {isAdmin && activeViewMode === 'studio' ? (
        <div className="flex-1 grid grid-cols-12 overflow-hidden h-full">
          {/* COLUMN 1: Category Tree & Navigator (Left) */}
          <aside className="col-span-3 border-r border-[#2A2E35] bg-[#1A1D21] p-4 flex flex-col gap-4 overflow-y-auto">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
                <FolderPlus className="w-4 h-4 text-[#FF5500]" />
                Категории
              </span>
              <button
                onClick={() => setShowCatModal(true)}
                className="text-xs text-[#FF5500] hover:text-[#E04B00] font-semibold flex items-center gap-1"
              >
                <Plus className="w-3.5 h-3.5" /> Добавить
              </button>
            </div>

            <div className="space-y-2">
              {categories.map((cat, idx) => (
                <div key={cat.id} className="space-y-1">
                  <div
                    onClick={() => setActiveCatId(cat.id)}
                    className={`group p-2.5 rounded-lg border text-xs font-semibold flex items-center justify-between cursor-pointer transition-all ${
                      activeCatId === cat.id
                        ? 'bg-[#FF5500]/10 border-[#FF5500] text-[#FF5500]'
                        : 'bg-[#121417] border-[#2A2E35] text-slate-300 hover:border-slate-600'
                    }`}
                  >
                    <span className="break-words leading-snug flex-1 flex items-start gap-2">
                      📁 {cat.title}
                    </span>
                    <div className="flex items-center gap-1 shrink-0">
                      <button
                        onClick={(e) => { e.stopPropagation(); moveCategory(idx, 'up'); }}
                        className="p-1 hover:text-white text-slate-500"
                      >
                        <ChevronUp className="w-3 h-3" />
                      </button>
                      <button
                        onClick={(e) => { e.stopPropagation(); moveCategory(idx, 'down'); }}
                        className="p-1 hover:text-white text-slate-500"
                      >
                        <ChevronDown className="w-3 h-3" />
                      </button>
                    </div>
                  </div>

                  {/* Sub-guides for active category */}
                  {activeCatId === cat.id && categoryDetail && (
                    <div className="pl-4 space-y-1 pt-1">
                      {categoryDetail.guides.map((g, gIdx) => (
                        <div
                          key={g.orig_idx}
                          onClick={() => selectGuide(g, gIdx)}
                          className={`p-2 rounded-md text-[11px] flex items-center justify-between cursor-pointer transition-colors group/g ${
                            activeGuideIdx === g.orig_idx
                              ? 'bg-[#FF5500] text-white font-medium'
                              : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'
                          }`}
                        >
                          <span className="break-words leading-snug flex-1">📄 {g.title}</span>
                          <div className="flex items-center gap-1 shrink-0">
                            {g.is_hidden && <span className="text-[9px] text-red-400 font-mono">[скрыт]</span>}
                            <button
                              onClick={(e) => { e.stopPropagation(); moveGuide(gIdx, 'up'); }}
                              className="p-0.5 hover:text-white text-slate-400 opacity-60 group-hover/g:opacity-100"
                              title="Переместить выше"
                            >
                              <ChevronUp className="w-3 h-3" />
                            </button>
                            <button
                              onClick={(e) => { e.stopPropagation(); moveGuide(gIdx, 'down'); }}
                              className="p-0.5 hover:text-white text-slate-400 opacity-60 group-hover/g:opacity-100"
                              title="Переместить ниже"
                            >
                              <ChevronDown className="w-3 h-3" />
                            </button>
                          </div>
                        </div>
                      ))}
                      <button
                        onClick={resetGuideForm}
                        className="w-full text-left p-2 rounded-md text-[11px] text-[#FF5500] hover:bg-[#FF5500]/10 font-semibold flex items-center gap-1"
                      >
                        <Plus className="w-3 h-3" /> Создать статью
                      </button>
                    </div>
                  )}
                </div>
              ))}
            </div>
          </aside>

          {/* COLUMN 2: Guide & Interactive Keyboard Editor (Center) */}
          <main className="col-span-5 p-6 overflow-y-auto space-y-6 bg-[#121417] h-full">
            <div className="space-y-4">
              <h2 className="text-base font-bold text-slate-100 flex items-center gap-2 border-b border-[#2A2E35] pb-3">
                <FileText className="w-4 h-4 text-[#FF5500]" />
                Редактор статьи и клавиатуры
              </h2>

              {/* Metadata Fields */}
              <div className="grid grid-cols-2 gap-3">
                <div className="col-span-2 space-y-1">
                  <div className="flex items-center justify-between">
                    <label className="text-xs text-slate-400 font-semibold">Заголовок статьи</label>
                    <label className="flex items-center gap-1.5 text-xs text-red-400 cursor-pointer font-medium">
                      <input
                        type="checkbox"
                        checked={guideIsHidden}
                        onChange={e => { setGuideIsHidden(e.target.checked); setAutoSaved(false); }}
                        className="accent-red-500"
                      />
                      Скрыть (Черновик)
                    </label>
                  </div>
                  <input
                    type="text"
                    value={guideTitle}
                    onChange={e => { setGuideTitle(e.target.value); setAutoSaved(false); }}
                    placeholder="Заголовок инструкции"
                    className="w-full bg-[#1A1D21] border border-[#2A2E35] rounded-lg px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-[#FF5500]"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs text-slate-400 font-semibold">Слаг / URL</label>
                  <input
                    type="text"
                    value={guideSlug}
                    onChange={e => { setGuideSlug(e.target.value); setAutoSaved(false); }}
                    placeholder="windows-setup"
                    className="w-full bg-[#1A1D21] border border-[#2A2E35] rounded-lg px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-[#FF5500]"
                  />
                </div>

                <div className="space-y-1">
                  <label className="text-xs text-slate-400 font-semibold">Превью для карточки бота</label>
                  <input
                    type="text"
                    value={guideSummary}
                    onChange={e => { setGuideSummary(e.target.value); setAutoSaved(false); }}
                    placeholder="Короткий анонс для чата"
                    className="w-full bg-[#1A1D21] border border-[#2A2E35] rounded-lg px-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-[#FF5500]"
                  />
                </div>
              </div>

              {/* Tags Selector */}
              <div className="space-y-1">
                <label className="text-xs text-slate-400 font-semibold flex items-center gap-1">
                  <TagIcon className="w-3 h-3 text-[#FF5500]" />
                  Теги и поиск (Enter для добавления)
                </label>
                <div className="bg-[#1A1D21] border border-[#2A2E35] rounded-lg p-2 flex flex-wrap gap-1.5 items-center">
                  {guideTags.map(tag => (
                    <span key={tag} className="bg-[#FF5500]/20 text-[#FF5500] border border-[#FF5500]/30 text-[10px] font-semibold px-2 py-0.5 rounded-md flex items-center gap-1">
                      #{tag}
                      <X className="w-3 h-3 cursor-pointer hover:text-white" onClick={() => removeTag(tag)} />
                    </span>
                  ))}
                  <input
                    type="text"
                    value={tagInput}
                    onChange={e => setTagInput(e.target.value)}
                    onKeyDown={handleAddTag}
                    placeholder="Добавить тег..."
                    className="bg-transparent text-xs text-slate-200 focus:outline-none px-1 py-0.5 flex-1 min-w-[100px]"
                  />
                </div>
              </div>

              {/* Content Markdown Editor */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="text-xs text-slate-400 font-semibold">Содержимое (Markdown)</label>
                  <div className="flex items-center gap-1 bg-[#1A1D21] border border-[#2A2E35] rounded-lg p-1">
                    <button onClick={() => insertFormatting('**')} className="p-1 hover:bg-slate-800 rounded text-slate-300" title="Жирный"><Bold className="w-3 h-3" /></button>
                    <button onClick={() => insertFormatting('*')} className="p-1 hover:bg-slate-800 rounded text-slate-300" title="Курсив"><Italic className="w-3 h-3" /></button>
                    <button onClick={() => insertFormatting('> ', false)} className="p-1 hover:bg-slate-800 rounded text-slate-300" title="Цитата"><Quote className="w-3 h-3" /></button>
                    <button onClick={() => insertFormatting('```', true)} className="p-1 hover:bg-slate-800 rounded text-slate-300" title="Блок кода"><Code className="w-3 h-3" /></button>
                  </div>
                </div>

                <textarea
                  value={guideContent}
                  onChange={e => { setGuideContent(e.target.value); setAutoSaved(false); }}
                  rows={8}
                  className="w-full bg-[#1A1D21] border border-[#2A2E35] rounded-lg p-3 text-xs font-mono text-slate-200 focus:outline-none focus:border-[#FF5500]"
                />
              </div>

              {/* Visual Inline Keyboard Builder */}
              <div className="space-y-3 pt-2">
                <div className="flex items-center justify-between border-t border-[#2A2E35] pt-4">
                  <span className="text-xs font-bold text-slate-200 uppercase tracking-wider">
                    Интерактивные кнопки (Inline-клавиатура)
                  </span>
                  <button
                    type="button"
                    onClick={addRow}
                    className="text-xs bg-[#FF5500]/10 hover:bg-[#FF5500]/20 text-[#FF5500] border border-[#FF5500]/30 font-semibold px-2.5 py-1 rounded-lg transition-colors"
                  >
                    + Добавить ряд
                  </button>
                </div>

                {guideRows.map((row, rIdx) => (
                  <div key={rIdx} className="bg-[#1A1D21] border border-[#2A2E35] p-3 rounded-xl space-y-2">
                    <div className="flex items-center justify-between text-[11px] text-[#FF5500] font-bold tracking-wider">
                      <span>РЯД {rIdx + 1}</span>
                      <button
                        type="button"
                        onClick={() => addButtonToRow(rIdx)}
                        className="text-[10px] text-slate-300 hover:text-white bg-[#2A2E35] px-2 py-0.5 rounded"
                      >
                        + Кнопка в ряд
                      </button>
                    </div>

                    <div className="space-y-2">
                      {row.buttons.map((btn, bIdx) => (
                        <div key={bIdx} className="bg-[#121417] p-2 rounded-lg border border-[#2A2E35] grid grid-cols-12 gap-2 items-center">
                          <input
                            type="text"
                            value={btn.text}
                            onChange={e => updateButton(rIdx, bIdx, 'text', e.target.value)}
                            placeholder="Текст кнопки"
                            className="col-span-4 bg-[#1A1D21] border border-[#2A2E35] text-[11px] text-slate-100 rounded px-2 py-1"
                          />
                          <select
                            value={btn.type}
                            onChange={e => updateButton(rIdx, bIdx, 'type', e.target.value)}
                            className="col-span-3 bg-[#1A1D21] border border-[#2A2E35] text-[11px] text-slate-300 rounded px-1.5 py-1"
                          >
                            <option value="miniapp">Mini App</option>
                            <option value="callback">Callback</option>
                            <option value="url">Ссылка</option>
                          </select>
                          <input
                            type="text"
                            value={btn.payload}
                            onChange={e => updateButton(rIdx, bIdx, 'payload', e.target.value)}
                            placeholder="URL / Payload"
                            className="col-span-4 bg-[#1A1D21] border border-[#2A2E35] text-[11px] text-slate-100 rounded px-2 py-1"
                          />
                          <button
                            type="button"
                            onClick={() => removeButton(rIdx, bIdx)}
                            className="col-span-1 text-slate-500 hover:text-red-400 flex justify-center"
                          >
                            <Trash2 className="w-3.5 h-3.5" />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </main>

          {/* COLUMN 3: Dual-Mode Smartphone Live Preview (Right Sidebar) */}
          <aside className="col-span-4 border-l border-[#2A2E35] bg-[#1A1D21] p-6 flex flex-col items-center justify-start gap-4 overflow-y-auto h-full">
            <div className="flex bg-[#121417] p-1 rounded-xl border border-[#2A2E35] w-full shrink-0">
              <button
                onClick={() => setPreviewMode('miniapp')}
                className={`flex-1 py-1.5 text-xs font-semibold rounded-lg flex items-center justify-center gap-1.5 transition-colors ${
                  previewMode === 'miniapp' ? 'bg-[#FF5500] text-white' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <Smartphone className="w-3.5 h-3.5" /> Telegram Mini App
              </button>
              <button
                onClick={() => setPreviewMode('telegram')}
                className={`flex-1 py-1.5 text-xs font-semibold rounded-lg flex items-center justify-center gap-1.5 transition-colors ${
                  previewMode === 'telegram' ? 'bg-[#FF5500] text-white' : 'text-slate-400 hover:text-slate-200'
                }`}
              >
                <MessageSquare className="w-3.5 h-3.5" /> Чат-бот Telegram
              </button>
            </div>

            {/* Smartphone Framed Mockup */}
            <div className="w-[320px] h-[580px] bg-[#121417] border-4 border-[#2A2E35] rounded-[36px] shadow-2xl p-4 flex flex-col justify-between overflow-hidden relative shrink-0">
              <div className="w-28 h-4 bg-[#2A2E35] rounded-b-xl mx-auto absolute top-0 left-1/2 -translate-x-1/2 z-20" />

              <div className="flex-1 mt-4 overflow-y-auto space-y-3 pt-2 pr-1">
                {previewMode === 'miniapp' ? (
                  <div className="space-y-3">
                    <div className="flex items-center justify-between border-b border-[#2A2E35] pb-2">
                      <span className="text-[10px] uppercase font-bold text-[#FF5500] bg-[#FF5500]/10 px-2 py-0.5 rounded">
                        {categoryDetail?.title || 'База знаний'}
                      </span>
                      <span className="text-[10px] font-mono text-slate-500">/{guideSlug}</span>
                    </div>

                    <h3 className="text-sm font-bold text-white tracking-tight">{guideTitle}</h3>

                    <div className="flex flex-wrap gap-1">
                      {guideTags.map(t => (
                        <span key={t} className="text-[9px] bg-slate-800 text-slate-300 px-1.5 py-0.5 rounded">
                          #{t}
                        </span>
                      ))}
                    </div>

                    <div
                      className="text-xs text-slate-300 leading-relaxed space-y-2 font-sans border-t border-[#2A2E35] pt-2"
                      dangerouslySetInnerHTML={renderCleanHtmlContent(guideContent)}
                    />

                    <div className="space-y-1.5 pt-3">
                      {guideRows.map((row, rIdx) => (
                        <div key={rIdx} className="grid gap-1.5" style={{ gridTemplateColumns: `repeat(${row.buttons.length || 1}, minmax(0, 1fr))` }}>
                          {row.buttons.map((btn, bIdx) => (
                            <button
                              key={bIdx}
                              className="bg-[#FF5500] hover:bg-[#E04B00] text-white text-[11px] font-semibold py-2 px-2 rounded-lg truncate text-center shadow"
                            >
                              {btn.text}
                            </button>
                          ))}
                        </div>
                      ))}
                    </div>
                  </div>
                ) : (
                  <div className="space-y-3 pt-4">
                    <div className="bg-[#18222D] border border-[#232E3C] p-3 rounded-2xl space-y-2 text-xs text-slate-200">
                      <div className="font-bold text-white text-xs">{guideTitle}</div>
                      <p className="text-[11px] text-slate-300">{guideSummary}</p>
                    </div>

                    <div className="space-y-1">
                      {guideRows.map((row, rIdx) => (
                        <div key={rIdx} className="grid gap-1" style={{ gridTemplateColumns: `repeat(${row.buttons.length || 1}, minmax(0, 1fr))` }}>
                          {row.buttons.map((btn, bIdx) => (
                            <button
                              key={bIdx}
                              className="bg-[#2B5278] hover:bg-[#1E3B57] text-white text-[11px] font-semibold py-2 px-2 rounded-lg truncate text-center shadow"
                            >
                              {btn.text}
                            </button>
                          ))}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </aside>
        </div>
      ) : (
        /* RENDER MODE B/C: PUBLIC DOC-STYLE KNOWLEDGE BASE READER (Independent Scroll Architecture) */
        <div className="flex-1 flex overflow-hidden relative h-full">
          {/* Mobile Drawer Backdrop */}
          {mobileDrawerOpen && (
            <div
              onClick={() => setMobileDrawerOpen(false)}
              className="fixed inset-0 bg-black/60 backdrop-blur-sm z-30 md:hidden"
            />
          )}

          {/* Left Navigation Sidebar (Independent Fixed Width & Scroll) */}
          <aside className={`
            fixed md:relative top-0 left-0 bottom-0 z-40 md:z-auto
            w-72 md:w-80 border-r border-[#2A2E35] bg-[#1A1D21] flex flex-col h-full shrink-0
            transition-transform duration-200 ease-in-out
            ${mobileDrawerOpen ? 'translate-x-0' : '-translate-x-full md:translate-x-0'}
          `}>
            {/* Fixed Search Bar Header Section */}
            <div className="p-4 border-b border-[#2A2E35] shrink-0">
              <div className="relative">
                <Search className="w-4 h-4 text-slate-400 absolute left-3 top-1/2 -translate-y-1/2" />
                <input
                  type="text"
                  value={searchQuery}
                  onChange={e => setSearchQuery(e.target.value)}
                  placeholder="Поиск по статьям..."
                  className="w-full bg-[#121417] border border-[#2A2E35] rounded-xl pl-9 pr-3 py-2 text-xs text-slate-100 focus:outline-none focus:border-[#FF5500]"
                />
              </div>
            </div>

            {/* Scrollable Tree Container */}
            <div className="flex-1 overflow-y-auto p-3 space-y-2">
              {publicCategories.map(cat => {
                const isExp = expandedCategories[cat.id] ?? true;
                const filteredGuides = cat.guides.filter(g =>
                  !searchQuery || g.title.toLowerCase().includes(searchQuery.toLowerCase()) || (g.tags && g.tags.some(t => t.toLowerCase().includes(searchQuery.toLowerCase())))
                );

                if (searchQuery && filteredGuides.length === 0) return null;

                return (
                  <div key={cat.id} className="space-y-1">
                    <button
                      onClick={() => toggleCategoryExpand(cat.id)}
                      className="w-full flex items-start justify-between p-2.5 rounded-xl text-xs font-bold text-slate-200 hover:bg-[#2A2E35]/50 transition-colors text-left gap-2"
                    >
                      <span className="shrink-0 text-sm">📁</span>
                      <span className="flex-1 break-words leading-snug">{cat.title}</span>
                      <ChevronRight className={`w-3.5 h-3.5 shrink-0 mt-0.5 transition-transform ${isExp ? 'rotate-90' : ''}`} />
                    </button>

                    {isExp && (
                      <div className="pl-3 space-y-1 border-l border-[#2A2E35] ml-2">
                        {filteredGuides.map(g => {
                          const isSel = selectedPublicGuide?.orig_idx === g.orig_idx && selectedPublicCategory?.id === cat.id;
                          return (
                            <button
                              key={g.orig_idx}
                              onClick={() => {
                                setSelectedPublicCategory(cat);
                                setSelectedPublicGuide(g);
                                setMobileDrawerOpen(false);
                              }}
                              className={`w-full flex items-start gap-2 p-2 rounded-lg text-xs text-left transition-colors ${
                                isSel
                                  ? 'bg-[#FF5500]/10 text-[#FF5500] font-bold border border-[#FF5500]/30'
                                  : 'text-slate-300 hover:bg-[#2A2E35]/70 hover:text-slate-100'
                              }`}
                            >
                              <span className="shrink-0 text-xs mt-0.5">📄</span>
                              <span className="flex-1 break-words leading-snug">{g.title}</span>
                            </button>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </aside>

          {/* Main Article Content Area (Independent Vertical Scroll) */}
          <main className="flex-1 h-full overflow-y-auto p-4 md:p-8 bg-[#121417]">
            {selectedPublicGuide ? (
              <div className="max-w-4xl mx-auto space-y-6 pt-2">
                {/* Category Breadcrumb */}
                <div className="text-xs text-[#FF5500] font-semibold uppercase tracking-wider flex items-center gap-2">
                  <span>{selectedPublicCategory?.title || 'База знаний'}</span>
                  <span>/</span>
                  <span className="text-slate-400 font-mono text-[11px]">{selectedPublicGuide.slug || 'article'}</span>
                </div>

                {/* Article Header */}
                <h1 className="text-2xl font-extrabold text-white tracking-tight break-words">{selectedPublicGuide.title}</h1>

                {selectedPublicGuide.tags && selectedPublicGuide.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1.5">
                    {selectedPublicGuide.tags.map(t => (
                      <span key={t} className="text-[10px] bg-[#1A1D21] border border-[#2A2E35] text-[#FF5500] font-semibold px-2.5 py-0.5 rounded-md">
                        #{t}
                      </span>
                    ))}
                  </div>
                )}

                {/* Clean Formatted Article Body with Tailwind Prose Typography */}
                <div
                  className="prose prose-invert max-w-none text-slate-300 text-sm leading-relaxed
                             [&_p]:mb-3 [&_h3]:text-base [&_h3]:font-bold [&_h3]:text-slate-100 [&_h3]:mt-4 [&_h3]:mb-2
                             [&_a]:text-[#FF5500] [&_a]:underline [&_ul]:list-disc [&_ul]:pl-5 [&_ol]:list-decimal [&_ol]:pl-5
                             [&_li]:mb-1 [&_strong]:text-white [&_em]:italic border-t border-[#2A2E35] pt-6"
                  dangerouslySetInnerHTML={renderCleanHtmlContent(selectedPublicGuide.content || selectedPublicGuide.text)}
                />

                {/* Clean Interactive Action Buttons (NO Admin Row Markers) */}
                {selectedPublicGuide.buttons && selectedPublicGuide.buttons.length > 0 && (
                  <div className="space-y-2 border-t border-[#2A2E35] pt-6">
                    <span className="text-xs font-bold text-slate-400 uppercase tracking-wider block mb-2">Быстрые действия</span>
                    {selectedPublicGuide.buttons.map((row, rIdx) => (
                      <div key={rIdx} className="grid gap-2" style={{ gridTemplateColumns: `repeat(${row.buttons.length || 1}, minmax(0, 1fr))` }}>
                        {row.buttons.map((btn, bIdx) => (
                          <button
                            key={bIdx}
                            onClick={() => handlePublicButtonClick(btn)}
                            className="bg-[#FF5500] hover:bg-[#E04B00] text-white text-xs font-semibold py-2.5 px-3 rounded-xl transition-colors flex items-center justify-center gap-1.5 shadow-md shadow-[#FF5500]/10"
                          >
                            {btn.text}
                            <ExternalLink className="w-3.5 h-3.5 opacity-80" />
                          </button>
                        ))}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            ) : (
              <div className="text-center py-20 text-slate-500 text-xs">
                Выберите статью из меню слева.
              </div>
            )}
          </main>
        </div>
      )}

      {/* Telegram Admin Login Modal */}
      {showLoginModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#1A1D21] border border-[#2A2E35] p-6 rounded-xl max-w-sm w-full space-y-4 text-center">
            <h3 className="text-base font-bold text-white">Авторизация Администратора</h3>
            <p className="text-xs text-slate-400">Нажмите на кнопку ниже, чтобы войти через Telegram:</p>
            <div id="modal-telegram-widget" className="flex justify-center py-2 min-h-[50px] items-center">
              <span className="text-xs text-slate-500">Загрузка виджета...</span>
            </div>
            <button
              type="button"
              onClick={() => setShowLoginModal(false)}
              className="w-full py-1.5 bg-[#2A2E35] text-xs font-semibold text-slate-300 rounded-lg hover:bg-slate-700"
            >
              Отмена
            </button>
          </div>
        </div>
      )}

      {/* Quick Add Category Modal */}
      {showCatModal && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-[#1A1D21] border border-[#2A2E35] p-6 rounded-xl max-w-sm w-full space-y-4">
            <h3 className="text-base font-bold text-white flex items-center gap-2">
              <FolderPlus className="w-4 h-4 text-[#FF5500]" />
              Новая категория
            </h3>

            <form onSubmit={handleAddCategory} className="space-y-3">
              <div>
                <label className="text-xs text-slate-400 font-semibold">ID категории (slug)</label>
                <input
                  type="text"
                  value={newCatId}
                  onChange={e => setNewCatId(e.target.value)}
                  placeholder="напр. windows"
                  required
                  className="w-full bg-[#121417] border border-[#2A2E35] text-xs rounded-lg px-3 py-2 text-slate-100 mt-1"
                />
              </div>

              <div>
                <label className="text-xs text-slate-400 font-semibold">Название</label>
                <input
                  type="text"
                  value={newCatTitle}
                  onChange={e => setNewCatTitle(e.target.value)}
                  placeholder="напр. 🖥️ Настройка Windows"
                  required
                  className="w-full bg-[#121417] border border-[#2A2E35] text-xs rounded-lg px-3 py-2 text-slate-100 mt-1"
                />
              </div>

              <div className="flex justify-end gap-2 pt-2">
                <button
                  type="button"
                  onClick={() => setShowCatModal(false)}
                  className="px-3 py-1.5 bg-[#2A2E35] text-xs font-semibold text-slate-300 rounded-lg hover:bg-slate-700"
                >
                  Отмена
                </button>
                <button
                  type="submit"
                  className="px-4 py-1.5 bg-[#FF5500] text-xs font-semibold text-white rounded-lg hover:bg-[#E04B00]"
                >
                  Создать
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
