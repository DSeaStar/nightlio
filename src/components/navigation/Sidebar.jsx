import { Home, BarChart3, Trophy, Settings, Target } from 'lucide-react';
import { useEffect } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useT } from '../../i18n/I18nContext';

const Sidebar = ({ onLoadStatistics }) => {
  const t = useT();
  const items = [
    { key: '/dashboard', label: t('nav.home'), icon: Home, end: true },
    { key: '/dashboard/goals', label: t('nav.goals'), icon: Target },
    { key: '/dashboard/stats', label: t('nav.statistics'), icon: BarChart3 },
    { key: '/dashboard/achievements', label: t('nav.achievements'), icon: Trophy },
  ];

  const location = useLocation();

  useEffect(() => {
    if (location.pathname.includes('stats') && typeof onLoadStatistics === 'function') {
      onLoadStatistics();
    }
  }, [location.pathname, onLoadStatistics]);

  return (
    <aside className={`sidebar`}>
      <div className="sidebar__inner">
        <div className="sidebar__brand" style={{ alignItems: 'flex-start', flexDirection: 'column', gap: '0.75rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{ width: 36, height: 36, borderRadius: 10, background: 'transparent', display: 'grid', placeItems: 'center', color: 'var(--text)', overflow: 'hidden' }}>
              <img
                src={'/logo.png'}
                alt="Nightlio"
                style={{ width: '100%', height: '100%', objectFit: 'contain', display: 'block', background: 'transparent', outline: 'none' }}
              />
            </div>
            <strong style={{ color: 'var(--text)', letterSpacing: '-0.01em', fontSize: '1.5rem', fontWeight: '700' }}>{t('app.name')}</strong>
          </div>
          <span style={{ color: 'var(--text)' , opacity: 0.85, fontSize: '0.875rem', paddingLeft: '0.25rem' }}>{t('app.tagline')}</span>
        </div>

        <div className="sidebar__sections">
          {items.map(({ key, label, icon: Icon, end }) => (
            <NavLink
              key={key}
              to={key}
              end={end}

              className={({ isActive }) => `sidebar__item ${isActive ? 'is-active' : ''}`}
              title={label}
            >
              <Icon size={18} style={{ flexShrink: 0 }} />
              <span>{label}</span>
            </NavLink>
          ))}
        </div>

        <div className="sidebar__footer">
          <NavLink
            to="/dashboard/settings"
            className={({ isActive }) => `sidebar__item ${isActive ? 'is-active' : ''}`}
            title={t('nav.settings')}
          >
            <Settings size={18} style={{ flexShrink: 0 }} />
            <span>{t('nav.settings')}</span>
          </NavLink>
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;
