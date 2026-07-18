import { useConfig } from '../contexts/ConfigContext';
import { useI18n, useT } from '../i18n/I18nContext';

const SettingsView = () => {
  const { config, loading } = useConfig();
  const t = useT();
  const { locale, setLocale } = useI18n();

  const featureFlags = [
    {
      key: 'enable_google_oauth',
      label: t('settings.googleLogin'),
      description: t('settings.googleLoginDesc'),
    },
    {
      key: 'enable_mood_music',
      label: t('settings.moodMusic'),
      description: t('settings.moodMusicDesc'),
    },
    {
      key: 'enable_ai_insights',
      label: t('ai.settingsLabel'),
      description: t('ai.settingsDesc'),
    },
  ];

  const sectionStyle = {
    marginTop: '1rem',
    border: '1px solid var(--border)',
    borderRadius: '12px',
    padding: '1rem',
    background: 'var(--surface)',
  };

  return (
    <div style={{ textAlign: 'left' }}>
      <h2 style={{ marginTop: 0, color: 'var(--text)' }}>{t('settings.title')}</h2>

      <section style={sectionStyle} aria-label={t('settings.language')}>
        <h3 style={{ marginTop: 0, marginBottom: '0.5rem', color: 'var(--text)' }}>
          {t('settings.language')}
        </h3>
        <p style={{ marginTop: 0, marginBottom: '0.75rem', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
          {t('common.languageHint')}
        </p>
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          {[
            { code: 'zh', label: t('common.chinese') },
            { code: 'en', label: t('common.english') },
          ].map((opt) => {
            const active = locale === opt.code;
            return (
              <button
                key={opt.code}
                type="button"
                onClick={() => setLocale(opt.code)}
                aria-pressed={active}
                style={{
                  padding: '0.5rem 1rem',
                  borderRadius: '10px',
                  border: `1px solid ${active ? 'var(--accent, #6366f1)' : 'var(--border)'}`,
                  background: active ? 'var(--accent, #6366f1)' : 'transparent',
                  color: active ? '#fff' : 'var(--text)',
                  cursor: 'pointer',
                  fontWeight: active ? 600 : 400,
                }}
              >
                {opt.label}
              </button>
            );
          })}
        </div>
      </section>

      <section style={sectionStyle} aria-label={t('settings.featureFlags')}>
        <h3 style={{ marginTop: 0, marginBottom: '0.5rem', color: 'var(--text)' }}>
          {t('settings.featureFlags')}
        </h3>
        <p style={{ marginTop: 0, marginBottom: '0.75rem', color: 'var(--text-muted)', fontSize: '0.9rem' }}>
          {t('settings.featureFlagsHint')}
        </p>

        {featureFlags.map((flag) => {
          const isEnabled = Boolean(config[flag.key]);
          return (
            <label
              key={flag.key}
              style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: '0.75rem',
                padding: '0.5rem 0',
                borderTop: '1px solid var(--border)',
              }}
            >
              <input
                type="checkbox"
                checked={isEnabled}
                readOnly
                disabled
                aria-label={flag.label}
                style={{ marginTop: '0.15rem' }}
              />
              <span>
                <strong style={{ color: 'var(--text)' }}>{flag.label}</strong>
                <span style={{ display: 'block', color: 'var(--text-muted)', fontSize: '0.86rem' }}>
                  {flag.description}
                  {loading
                    ? ` (${t('common.loading')})`
                    : isEnabled
                      ? ` (${t('common.enabled')})`
                      : ` (${t('common.disabled')})`}
                </span>
              </span>
            </label>
          );
        })}
      </section>
    </div>
  );
};

export default SettingsView;
