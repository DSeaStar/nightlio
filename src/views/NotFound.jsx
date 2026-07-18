import React from 'react';
import { Link } from 'react-router-dom';
import { useT } from '../i18n/I18nContext';

const NotFound = () => {
  const t = useT();
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      height: '100vh',
      textAlign: 'center',
      padding: '2rem',
      color: 'var(--text)'
    }}>
      <h1 style={{ fontSize: '4rem', marginBottom: '1rem' }}>404</h1>
      <p style={{ fontSize: '1.5rem', marginBottom: '2rem' }}>{t('notFound.title')}</p>
      <Link to="/" style={{
        padding: '0.75rem 1.5rem',
        backgroundColor: 'var(--primary)',
        color: 'white',
        textDecoration: 'none',
        borderRadius: 'var(--radius)',
        fontWeight: '500'
      }}>
        {t('notFound.backHome')}
      </Link>
    </div>
  );
};

export default NotFound;
