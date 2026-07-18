import { useState } from 'react';
import { Sparkles, Loader2, X } from 'lucide-react';
import apiService from '../../services/api';
import { useConfig } from '../../contexts/ConfigContext';
import { useI18n, useT } from '../../i18n/I18nContext';
import { useToast } from '../ui/ToastProvider';

const sentimentLabelKey = {
  positive: 'ai.sentimentPositive',
  neutral: 'ai.sentimentNeutral',
  negative: 'ai.sentimentNegative',
  mixed: 'ai.sentimentMixed',
};

/**
 * AI insights for recent journals — button intended next to History on home.
 */
const AiInsightsPanel = ({
  history = [],
  limit = 14,
  compact = false,
}) => {
  const t = useT();
  const { locale } = useI18n();
  const { config } = useConfig();
  const { show } = useToast();
  const [open, setOpen] = useState(false);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');

  const enabled = Boolean(config?.enable_ai_insights);
  const entries = (history || []).filter((e) => e && (e.content || e.mood != null));

  const runInsights = async () => {
    if (!entries.length) {
      show(t('ai.needHistory'), 'info');
      return;
    }

    setOpen(true);
    setLoading(true);
    setError('');
    setResult(null);

    try {
      const data = await apiService.getAiInsights({
        history: entries.slice(0, limit).map((e) => ({
          date: e.date,
          mood: e.mood,
          content: e.content,
        })),
        limit,
        locale,
      });
      setResult(data);
    } catch (err) {
      const msg = err?.message || t('ai.failed');
      setError(msg);
      show(msg, 'error');
    } finally {
      setLoading(false);
    }
  };

  if (!enabled) {
    return null;
  }

  return (
    <>
      <button
        type="button"
        onClick={() => { void runInsights(); }}
        disabled={loading}
        style={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: '0.4rem',
          padding: compact ? '0.4rem 0.85rem' : '0.55rem 1.1rem',
          borderRadius: '999px',
          border: '1px solid var(--border)',
          background: 'linear-gradient(135deg, color-mix(in oklab, var(--accent-600), #7c3aed 40%), var(--accent-600))',
          color: '#fff',
          cursor: loading ? 'wait' : 'pointer',
          fontWeight: 600,
          fontSize: compact ? '0.82rem' : '0.9rem',
          boxShadow: 'var(--shadow-md)',
          opacity: loading ? 0.85 : 1,
          whiteSpace: 'nowrap',
          flexShrink: 0,
        }}
      >
        {loading ? <Loader2 size={15} className="is-spinning" /> : <Sparkles size={15} />}
        {loading ? t('ai.generating') : t('ai.button')}
      </button>

      {open && (
        <div
          style={{
            flexBasis: '100%',
            width: '100%',
            marginTop: '0.35rem',
            marginBottom: '0.75rem',
            border: '1px solid var(--border)',
            borderRadius: '16px',
            background: 'var(--bg-card)',
            boxShadow: 'var(--shadow-lg)',
            padding: '1rem 1.1rem',
            textAlign: 'left',
          }}
          role="region"
          aria-label={t('ai.title')}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: '0.75rem' }}>
            <h3 style={{ margin: 0, color: 'var(--text)', fontSize: '1.05rem', display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <Sparkles size={18} />
              {t('ai.title')}
            </h3>
            <button
              type="button"
              onClick={() => setOpen(false)}
              aria-label={t('common.cancel')}
              style={{
                background: 'transparent',
                border: 'none',
                color: 'var(--text-muted)',
                cursor: 'pointer',
                padding: '0.25rem',
              }}
            >
              <X size={18} />
            </button>
          </div>

          <p style={{ margin: '0.5rem 0 0', fontSize: '0.82rem', color: 'var(--text-muted)' }}>
            {t('ai.basedOnRecent', { n: Math.min(entries.length, limit) })}
          </p>

          {loading && (
            <p style={{ margin: '1rem 0 0', color: 'var(--text-muted)' }}>{t('ai.generatingHint')}</p>
          )}

          {error && !loading && (
            <p style={{ margin: '1rem 0 0', color: 'var(--accent-600)' }}>{error}</p>
          )}

          {result && !loading && (
            <div style={{ marginTop: '0.85rem', display: 'flex', flexDirection: 'column', gap: '0.9rem' }}>
              <section>
                <h4 style={sectionTitle}>{t('ai.summary')}</h4>
                <p style={bodyText}>{result.summary || '—'}</p>
              </section>

              <section>
                <h4 style={sectionTitle}>{t('ai.sentiment')}</h4>
                <p style={bodyText}>
                  {t(sentimentLabelKey[result.sentiment?.label] || 'ai.sentimentMixed')}
                  {typeof result.sentiment?.score === 'number'
                    ? ` · ${Math.round(result.sentiment.score * 100)}%`
                    : ''}
                </p>
                {!!result.sentiment?.emotions?.length && (
                  <div style={chipRow}>
                    {result.sentiment.emotions.map((e) => (
                      <span key={e} style={chip}>{e}</span>
                    ))}
                  </div>
                )}
              </section>

              <section>
                <h4 style={sectionTitle}>{t('ai.tags')}</h4>
                {result.tags?.length ? (
                  <div style={chipRow}>
                    {result.tags.map((tag) => (
                      <span key={tag} style={chip}>{tag}</span>
                    ))}
                  </div>
                ) : (
                  <p style={bodyText}>—</p>
                )}
              </section>

              <section>
                <h4 style={sectionTitle}>{t('ai.trend')}</h4>
                <p style={bodyText}>{result.trend_prediction || '—'}</p>
              </section>

              <section>
                <h4 style={sectionTitle}>{t('ai.suggestions')}</h4>
                {result.suggestions?.length ? (
                  <ul style={{ margin: '0.35rem 0 0', paddingLeft: '1.2rem', color: 'var(--text)' }}>
                    {result.suggestions.map((s, i) => (
                      <li key={i} style={{ marginBottom: '0.35rem' }}>{s}</li>
                    ))}
                  </ul>
                ) : (
                  <p style={bodyText}>—</p>
                )}
              </section>

              {result.model && (
                <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                  {t('ai.model', { model: result.model })}
                  {result.entry_count ? ` · ${t('ai.entryCount', { n: result.entry_count })}` : ''}
                </p>
              )}
            </div>
          )}
        </div>
      )}
    </>
  );
};

const sectionTitle = {
  margin: '0 0 0.35rem',
  fontSize: '0.85rem',
  fontWeight: 600,
  color: 'var(--accent-600)',
  letterSpacing: '0.02em',
};

const bodyText = {
  margin: 0,
  color: 'var(--text)',
  lineHeight: 1.55,
  fontSize: '0.92rem',
  whiteSpace: 'pre-wrap',
};

const chipRow = {
  display: 'flex',
  flexWrap: 'wrap',
  gap: '0.4rem',
  marginTop: '0.35rem',
};

const chip = {
  padding: '0.25rem 0.65rem',
  borderRadius: '999px',
  background: 'var(--surface)',
  border: '1px solid var(--border)',
  color: 'var(--text)',
  fontSize: '0.8rem',
};

export default AiInsightsPanel;
