# src/etl_pipeline.py
import sys
import logging
from extract import load_csv, fetch_channel_stats, fetch_channel_stats_mock
from transform import fix_types, handle_missing, merge_channel_stats, engineer_features
from load import save_to_sqlite, save_to_parquet

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

def run_pipeline(use_mock=False):
    log.info("Запуск ETL-пайплайна...")
    
    # 1. ЭТАП EXTRACT
    videos_df = load_csv('raw/Youtube_Data.csv')
    
    if use_mock:
        log.info("Используются mock-данные для каналов.")
        channels_df = fetch_channel_stats_mock()
    else:
        # Здесь логика подгрузки реального ключа из .env
        import os
        from dotenv import load_dotenv
        load_dotenv()
        api_key = os.getenv("YOUTUBE_API_KEY")
        
        if not api_key:
            log.warning("API-ключ не найден! Переключаемся на mock-данные.")
            channels_df = fetch_channel_stats_mock()
        else:
            unique_channels = videos_df['channel_id'].dropna().unique().tolist()
            channels_df = fetch_channel_stats(unique_channels, api_key)
            
    # 2. ЭТАП TRANSFORM
    df_transformed = fix_types(videos_df)
    df_transformed = handle_missing(df_transformed)
    df_transformed = merge_channel_stats(df_transformed, channels_df)
    df_final = engineer_features(df_transformed)
    
    # 3. ЭТАП LOAD
    save_to_sqlite(df_final, channels_df, 'data/youtube.db')
    save_to_parquet(df_final, 'data/features.parquet')
    
    log.info("ETL-пайплайн успешно завершен!")

if __name__ == '__main__':
    # Проверяем, передан ли флаг --mock при запуске
    mock_flag = '--mock' in sys.argv
    run_pipeline(use_mock=mock_flag)
