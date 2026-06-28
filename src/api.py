# src/api.py
from flask import Flask, request, jsonify
import joblib
import pandas as pd
import os

app = Flask(__name__)

# Указываем правильный путь к сохранённому файлу модели .pkl
# (Мы сохранили её шагом ранее из ноутбука)
MODEL_PATH = os.path.join(os.path.dirname(__file__), '../models/youtube_rf_model.pkl')

try:
    # ТУТ МЫ ЗАГРУЖАЕМ МОДЕЛЬ, А НЕ СОХРАНЯЕМ ЕЁ!
    model = joblib.load(MODEL_PATH)
    print("Успех: Модель загружена в API-сервер!")
except Exception as e:
    print(f"Ошибка загрузки модели: {e}")
    model = None

@app.route('/predict', methods=['POST'])
def predict():
    if not model:
        return jsonify({'error': 'Модель не доступна на сервере'}), 500
    try:
        # Получаем данные от пользователя в формате JSON
        data = request.get_json()
        
        # Превращаем JSON в DataFrame из одной строчки для модели
        input_df = pd.DataFrame([data])
        
        # Делаем предсказание просмотров
        prediction = model.predict(input_df)
        
        # Возвращаем ответ
        return jsonify({
            'status': 'success',
            'predicted_views': int(prediction[0])
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    # Запуск сервера на локальном хосте и порту 5000
    app.run(host='127.0.0.1', port=5000, debug=True)
