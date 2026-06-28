# src/load.py
import sqlite3
import os
import pandas as pd
import logging

log = logging.getLogger(__name__)

def save_to_sqlite(videos_df: pd.DataFrame, channel_df: pd.DataFrame, db_path: str = 'data/youtube.db'):
    """
    Сохраняет два датасета в SQLite и создаёт индексы.
    """
    # Создаем папку data/, если её вдруг нет
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    
    conn = sqlite3.connect(db_path)
    
    # Основная таблица с видео и всеми признаками
    videos_df.to_sql('ml_features', conn, if_exists='replace', index=False)
    conn.execute('CREATE INDEX IF NOT EXISTS idx_cat ON ml_features(category)')
    conn.execute('CREATE INDEX IF NOT EXISTS idx_chan ON ml_features(channel_id)')
    
    # Таблица со статистикой каналов (из YouTube API)
    channel_df.to_sql('channel_stats', conn, if_exists='replace', index=False)
    
    conn.commit()
    conn.close()
    
    log.info(f'SQLite сохранён: {db_path}')
    log.info(f' ml_features: {len(videos_df)} строк')
    log.info(f' channel_stats: {len(channel_df)} строк')

def save_to_parquet(df: pd.DataFrame, path: str = 'data/features.parquet'):
    """
    Сохраняет финальный датасет в формате Parquet.
    """
    # Создаем папку data/, если её вдруг нет
    os.makedirs(os.path.dirname(path), exist_ok=True)
    
    df.to_parquet(path, compression='snappy', index=False)
    size_kb = os.path.getsize(path) / 1024
    log.info(f'Parquet: {len(df)} строк -> {path} ({size_kb:.1f} KB)')
