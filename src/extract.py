# src/extract.py
import pandas as pd
import requests
import time
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

def load_csv(path: str = 'raw/Youtube_Data.csv') -> pd.DataFrame:
    """
    Загружает сырой CSV-файл датасета.
    """
    df = pd.read_csv(path, on_bad_lines='skip', engine='python')
    log.info(f'CSV загружен: {df.shape[0]} строк, {df.shape[1]} столбцов')
    log.info(f'Столбцы: {list(df.columns)}')
    return df

def fetch_channel_stats(channel_ids: list, api_key: str) -> pd.DataFrame:
    """
    Запрашивает статистику каналов через YouTube Data API v3.
    """
    BASE_URL = 'https://googleapis.com'
    ids_joined = ','.join(channel_ids)
    params = {
        'part': 'statistics',
        'id': ids_joined,
        'key': api_key,
        'maxResults': 50,
    }
    
    items = []
    for attempt in range(3):
        try:
            resp = requests.get(BASE_URL, params=params, timeout=10)
            resp.raise_for_status()
            items = resp.json().get('items', [])
            break
        except requests.exceptions.Timeout:
            log.warning(f'Попытка {attempt+1}: timeout, ожидаем 5 сек...')
            time.sleep(5)
        except requests.exceptions.HTTPError as e:
            log.error(f'HTTP-ошибка: {e.response.status_code} — {e}')
            raise

    records = []
    for item in items:
        stats = item.get('statistics', {})
        records.append({
            'channel_id': item['id'],
            'subscriber_count': int(stats.get('subscriberCount', 0)),
            'channel_total_views': int(stats.get('viewCount', 0)),
            'channel_video_count': int(stats.get('videoCount', 0)),
        })
    df = pd.DataFrame(records)
    log.info(f'API: получена статистика для {len(df)} каналов')
    return df

def fetch_channel_stats_mock() -> pd.DataFrame:
    """
    Заглушка на случай отсутствия API-ключа.
    """
    data = [
        ('UCsQBsZJltmLzlsJNG7HevBg', 8_100_000, 1_800_000_000, 145), # Tyler the Creator
        ('UC9YydG57epLqxA9cTzZXSeQ', 21_400_000, 5_600_000_000, 980), # Call of Duty
        ('UCBcRF18a7Qf58cCRy5xuWwQ', 6_300_000, 900_000_000, 430),  # Пример
    ]
    cols = ['channel_id', 'subscriber_count', 'channel_total_views', 'channel_video_count']
    return pd.DataFrame(data, columns=cols)
