import { Home, BarChart3, Trophy, Settings, Target } from 'lucide-react';
import { useEffect } from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { useT } from '../../i18n/I18nContext';

const BottomNav = ({ onLoadStatistics }) => {
  const t = useT();
  const items = [
    { key: '/dashboard', label: t('nav.home'), icon: Home, end: true },
    { key: '/dashboard/goals', label: t('nav.goals'), icon: Target },
    { key: '/dashboard/stats', label: t('nav.stats'), icon: BarChart3 },
    { key: '/dashboard/achievements', label: t('nav.awards'), icon: Trophy },
    { key: '/dashboard/settings', label: t('nav.settings'), icon: Settings },
  ];

  const location = useLocation();

  useEffect(() => {
    if (location.pathname.includes('stats') && typeof onLoadStatistics === 'function') {
      onLoadStatistics();
    }
  }, [location.pathname, onLoadStatistics]);

  return (
    <nav className="bottom-nav">
      {items.map(({ key, label, icon: Icon, end }) => (
        <NavLink
          key={key}
          to={key}
          end={end}

          className={({ isActive }) => `bottom-nav__item ${isActive ? 'is-active' : ''}`}
          aria-label={label}
        >
          <Icon size={20} />
          <span className="bottom-nav__label">{label}</span>
        </NavLink>
      ))}
    </nav>
  );
};

export default BottomNav;
