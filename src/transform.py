import pandas as pd 
import numpy as np 
import re 
import logging 
 
log = logging.getLogger(__name__) 
 
# Категории: маппинг ID -> название 
CATEGORY_MAP = { 
    1:  'Film & Entertainment', 
    2:  'Other',    # Autos & Vehicles — только 1 видео, объединяем 
    10: 'Music', 
    20: 'Gaming', 
    24: 'Other',    # Entertainment — только 1 видео, объединяем 
} 
 
# Константные столбцы — удаляем всегда 
CONSTANT_COLS = ['definition', 'caption', 'favorite_count'] 
 
 
def fix_types(df: pd.DataFrame) -> pd.DataFrame: 
   
    # Удаление констант 
    df = df.drop(columns=[c for c in CONSTANT_COLS if c in df.columns]) 
    log.info(f'Удалены константные столбцы: {CONSTANT_COLS}') 
 
    # Числовые типы 
    for col in ['view_count', 'like_count', 'comment_count']: 
        df[col] = pd.to_numeric(df[col], errors='coerce') 
 
    # Datetime 
    df['published_at'] = pd.to_datetime(df['published_at'], utc=True, errors='coerce') 
 
    # ISO 8601 duration -> секунды 
    def iso_to_sec(s): 
        if pd.isna(s): return None 
        h  = int(m.group(1)) if (m := re.search(r'(\d+)H', s)) else 0 
        mi = int(m.group(1)) if (m := re.search(r'(\d+)M', s)) else 0 
        sc = int(m.group(1)) if (m := re.search(r'(\d+)S', s)) else 0 
        return h * 3600 + mi * 60 + sc 
 
    df['duration_sec'] = df['duration'].apply(iso_to_sec) 
 
    # Категория: числовой ID -> текстовое название 
    df['category'] = df['category_id'].map(CATEGORY_MAP).fillna('Other') 
 
    log.info(f'Типы исправлены. Форма данных: {df.shape}') 
    return df 

def handle_missing(df: pd.DataFrame) -> pd.DataFrame: 
    
    n_before = len(df) 
 
    # Проверяем пропуски в числовых столбцах (их быть не должно) 
    num_nulls = df[['view_count', 'like_count', 'comment_count']].isnull().sum() 
    if num_nulls.any(): 
        log.warning(f'Пропуски в числовых столбцах: {num_nulls[num_nulls>0].to_dict()}') 
        df = df.dropna(subset=['view_count'])  # без цели обучение невозможно 
 
    # tags: NaN означает 'тегов нет' — не заполняем, а используем как флаг 
    # (признак has_tags создаётся на следующем шаге) 
    log.info(f'Пропуски в tags: {df["tags"].isnull().sum()} ({df["tags"].isnull().mean()*100:.1f}%)') 
    log.info(f'Удалено строк: {n_before - len(df)}') 
    return df

def merge_channel_stats(videos: pd.DataFrame, 
                         channel_stats: pd.DataFrame) -> pd.DataFrame: 
   
    n_before = len(videos) 
    df = videos.merge(channel_stats, on='channel_id', how='left') 
 
    # Проверяем, все ли каналы нашлись 
    missing = df['subscriber_count'].isnull().sum() 
    if missing > 0: 
        log.warning(f'{missing} видео без данных канала — заполняем нулями') 
        for col in ['subscriber_count', 'channel_total_views', 'channel_video_count']: 
            df[col] = df[col].fillna(0).astype(int) 
 
    assert len(df) == n_before, 'LEFT JOIN изменил количество строк!' 
    log.info(f'Merge выполнен: {len(df)} строк (изменений нет)') 
    return df

def engineer_features(df: pd.DataFrame) -> pd.DataFrame: 
    # --- Вовлечённость (из CSV) --- 
    safe = df['view_count'].replace(0, np.nan) 
    df['engagement_rate']  = df['like_count']    / safe 
    df['comment_rate']     = df['comment_count'] / safe 
    df['like_to_comment']  = df['like_count']    / (df['comment_count'] + 1) 
 
    # --- Текстовые признаки заголовка (из CSV) --- 
    df['title_length']     = df['title'].str.len() 
    df['title_word_count'] = df['title'].str.split().str.len() 
    df['title_upper_ratio']= df['title'].apply( 
        lambda t: sum(1 for c in t if c.isupper()) / max(len(t), 1)) 
 
    # --- Теги (из CSV) --- 
    df['has_tags']  = df['tags'].notna().astype(int) 
    df['tag_count'] = df['tags'].str.split(',').str.len().fillna(0).astype(int) 
 
    # --- Временные признаки (из CSV) --- 
    df['publish_hour'] = df['published_at'].dt.hour 
    # Примечание: publish_dayofweek показывает аномалию (97% — пн или вт), 
    # что, вероятно, отражает дату сбора данных, а не публикации. 
    # Включаем, но с низкими ожиданиями по важности. 
    df['publish_dayofweek'] = df['published_at'].dt.dayofweek 
# --- Преобразование длительности (из CSV) --- 
df['log_duration'] = np.log1p(df['duration_sec']) 
# --- Признаки канала (из YouTube API — второй источник) --- 
df['log_subscribers']       
= np.log1p(df.get('subscriber_count', 0)) 
df['log_channel_videos']    = np.log1p(df.get('channel_video_count', 0)) 
df['log_channel_total_views']= np.log1p(df.get('channel_total_views', 0)) 
log.info(f'Feature engineering завершён. Итого признаков: {df.shape[1]}') 
return df