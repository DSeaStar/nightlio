import { useState, useEffect, useMemo } from 'react';
import Modal from '../components/ui/Modal';
import ProgressBar from '../components/ui/ProgressBar';
import AchievementNFT from '../components/nft/AchievementNFT';
import apiService from '../services/api';
import { useT } from '../i18n/I18nContext';

// All possible achievements (names/descriptions localized via t)
const getAllAchievements = (t) => [
  {
    achievement_type: 'first_entry',
    name: t('achievements.firstEntryName'),
    description: t('achievements.firstEntryDesc'),
    icon: 'Zap',
    rarity: 'common'
  },
  {
    achievement_type: 'week_warrior',
    name: t('achievements.weekWarriorName'),
    description: t('achievements.weekWarriorDesc'),
    icon: 'Flame',
    rarity: 'uncommon'
  },
  {
    achievement_type: 'consistency_king',
    name: t('achievements.consistencyKingName'),
    description: t('achievements.consistencyKingDesc'),
    icon: 'Crown',
    rarity: 'rare'
  },
  {
    achievement_type: 'data_lover',
    name: t('achievements.dataLoverName'),
    description: t('achievements.dataLoverDesc'),
    icon: 'BarChart3',
    rarity: 'uncommon'
  },
  {
    achievement_type: 'mood_master',
    name: t('achievements.moodMasterName'),
    description: t('achievements.moodMasterDesc'),
    icon: 'Target',
    rarity: 'legendary'
  }
];

const AchievementsView = () => {
  // Web3 removed
  const t = useT();
  const [achievements, setAchievements] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [active, setActive] = useState(null);
  const [progress, setProgress] = useState({});
  const catalog = useMemo(() => getAllAchievements(t), [t]);

  useEffect(() => {
    loadAchievements();
  }, []);

  const loadAchievements = async () => {
    try {
      setLoading(true);
      const [data, prog] = await Promise.all([
        apiService.getUserAchievements(),
        apiService.getAchievementsProgress(),
      ]);
      setAchievements(data);
      setProgress(prog || {});
    } catch (err) {
      setError(t('achievements.loadFailed'));
      console.error('Failed to load achievements:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ marginTop: '2rem', textAlign: 'center', color: 'var(--text-muted)' }}>
        {t('common.loading')}
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ marginTop: '2rem', textAlign: 'center', color: 'var(--accent-600)' }}>
        {error}
      </div>
    );
  }

  return (
    <div style={{ marginTop: '1.5rem' }}>

  {/* Web3 notice removed */}

      {/* Achievements Grid */}
      <div style={{
        display: 'flex',
        flexWrap: 'wrap',
        gap: '1rem',
        padding: 0,
        margin: 0,
        alignItems: 'stretch',
        alignContent: 'flex-start',
        width: '100%'
      }}>
        {/* All possible achievements */}
        {catalog.map((achievement, index) => {
          const unlockedAchievement = achievements.find(a => a.achievement_type === achievement.achievement_type);
          const isUnlocked = !!unlockedAchievement;
          const localized = {
            ...achievement,
            ...(unlockedAchievement || {}),
            name: achievement.name,
            description: achievement.description,
          };
          const p = progress[achievement.achievement_type] || null;
          const progressValue = isUnlocked ? undefined : (p ? p.current : 0);
          const progressMax = p ? p.max : 7;
          return (
            <div
              key={index}
              onClick={() => setActive(localized)}
              style={{
                cursor: 'pointer',
                flex: '1 1 300px',
                minWidth: 260,
                maxWidth: '100%',
                display: 'flex'
              }}
            >
              <AchievementNFT 
                achievement={localized}
                isUnlocked={isUnlocked}
                progressValue={progressValue}
                progressMax={progressMax}
              />
            </div>
          );
        })}
      </div>

      <Modal open={!!active} onClose={() => setActive(null)} title={active?.name || t('achievements.title')}>
        <p style={{ marginTop: 0 }}>{active?.description}</p>
        {!achievements.find(a => a.achievement_type === active?.achievement_type) && (() => {
          const p = progress[active?.achievement_type] || { current: 0, max: 7 };
          return <ProgressBar value={p.current || 0} max={p.max || 7} label={t('achievements.progress')} />;
        })()}
        <div style={{ marginTop: 12, fontSize: 13, color: 'var(--text-muted)' }}>
          {t('achievements.tips')}
        </div>
      </Modal>
    </div>
  );
};

export default AchievementsView;