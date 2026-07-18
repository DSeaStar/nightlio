import { useState, useEffect } from 'react';
import MoodPicker from '../components/mood/MoodPicker';
import HistoryList from '../components/history/HistoryList';
import { useI18n, useT } from '../i18n/I18nContext';

const HistoryView = ({ pastEntries, loading, error, onMoodSelect, onDelete, onEdit, renderOnlyHeader = false }) => {
  const [filteredEntries, setFilteredEntries] = useState(pastEntries);
  const t = useT();
  const { locale } = useI18n();
  const dateLocale = locale === 'zh' ? 'zh-CN' : 'en-US';
  
  // Update filtered entries when pastEntries changes (e.g. from global search)
  useEffect(() => {
    setFilteredEntries(pastEntries);
  }, [pastEntries]);
  
  const currentDate = new Date();
  const dateString = currentDate.toLocaleDateString(dateLocale, { 
    weekday: 'long', 
    year: 'numeric', 
    month: 'long', 
    day: 'numeric' 
  });
  const timeString = currentDate.toLocaleTimeString(dateLocale, { 
    hour: '2-digit', 
    minute: '2-digit',
    hour12: locale !== 'zh',
  });

  return (
    <>
      <div className="history-header">
        <MoodPicker onMoodSelect={onMoodSelect} />
        <div className="history-date">
          <h2 className="history-today-title">{t('common.today')}</h2>
          <div className="history-datetime-group">
            <span className="history-date-part">{dateString}</span>
            <span className="history-time-part">{timeString}</span>
          </div>
        </div>
      </div>

      {renderOnlyHeader ? null : (
        <HistoryList 
          entries={filteredEntries}
          loading={loading} 
          error={error} 
          onDelete={onDelete}
          onEdit={onEdit}
        />
      )}
    </>
  );
};

export default HistoryView;