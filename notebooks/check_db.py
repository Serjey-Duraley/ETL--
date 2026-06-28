#%%
import sqlite3
import pandas as pd

# 1. Подключаемся к нашей созданной базе данных
conn = sqlite3.connect('../data/youtube.db')

# 2. Пишем тот самый проверочный SQL-запрос из задания
query = """
SELECT 
    category,
    COUNT(*) AS video_count,
    ROUND(AVG(view_count)) AS avg_views,
    ROUND(AVG(engagement_rate), 4) AS avg_engagement_rate,
    ROUND(AVG(CAST(duration_sec AS FLOAT) / 60), 1) AS avg_duration_min
FROM ml_features
GROUP BY category
ORDER BY avg_views DESC;
"""

# 3. Выполняем запрос и загружаем результат в красивую таблицу Pandas
df_result = pd.read_sql_query(query, conn)

# 4. Закрываем соединение
conn.close()

# 5. Выводим результат на экран
df_result

# %%
