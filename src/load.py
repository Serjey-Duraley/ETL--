import sqlite3 
import pandas as pd 
import logging 
 
log = logging.getLogger(__name__) 
 
def save_to_sqlite(videos_df: pd.DataFrame, 
                   channel_df: pd.DataFrame, 
                   db_path: str = 'data/youtube.db'): 
    """ 
    Сохраняет два датасета в SQLite и создаёт индексы. 
    """ 
    conn = sqlite3.connect(db_path) 
 
    # Основная таблица с видео и всеми признаками 
    videos_df.to_sql('ml_features', conn, if_exists='replace', index=False) 
    conn.execute('CREATE INDEX IF NOT EXISTS idx_cat  ON ml_features(category)') 
    conn.execute('CREATE INDEX IF NOT EXISTS idx_chan ON ml_features(channel_id)') 
 
    # Таблица со статистикой каналов (из YouTube API) 
    channel_df.to_sql('channel_stats', conn, if_exists='replace', index=False) 
 
    conn.commit() 
    conn.close() 
    log.info(f'SQLite сохранён: {db_path}') 
    log.info(f'  ml_features: {len(videos_df)} строк') 
    log.info(f'  channel_stats: {len(channel_df)} строк') 

    