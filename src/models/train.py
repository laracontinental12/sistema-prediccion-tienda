import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, root_mean_squared_error
import joblib
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.services.supabase_client import get_supabase

def entrenar_modelo_demanda():
    supabase = get_supabase()
    
    # 1. Cargar datos de la Capa Oro
    response = supabase.table("gold_ventas_diarias").select("*").execute()
    data = response.data
    
    if not data:
        print("⚠️ No hay datos en 'gold_ventas_diarias' para entrenar.")
        return

    df = pd.DataFrame(data)
    
    # 2. Ingeniería de características temporales para ML
    df['fecha'] = pd.to_datetime(df['fecha'])
    df['dia_semana'] = df['fecha'].dt.weekday
    df['mes'] = df['fecha'].dt.month
    df['dia_mes'] = df['fecha'].dt.day
    
    # One-Hot Encoding para la variable categórica producto_id
    df = pd.get_dummies(df, columns=['producto_id'], drop_first=False)
    
    # 3. Definición de variables de entrada (X) y objetivo (y)
    columnas_excluir = ['id', 'fecha', 'total_unidades', 'total_ingresos', 'created_at']
    features = [c for c in df.columns if c not in columnas_excluir]
    
    X = df[features]
    y = df['total_unidades']
    
    # 4. División Train / Test
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # 5. Entrenamiento con Random Forest
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # 6. Evaluación del modelo
    predictions = model.predict(X_test)
    mae = mean_absolute_error(y_test, predictions)
    rmse = root_mean_squared_error(y_test, predictions)
    
    print(f"✅ Modelo entrenado exitosamente.")
    print(f"📊 Métricas -> MAE: {mae:.2f} unidades | RMSE: {rmse:.2f} unidades")
    
    # 7. Guardar el artefacto del modelo
    os.makedirs("src/models", exist_ok=True)
    ruta_modelo = "src/models/modelo_prediccion_demanda.pkl"
    joblib.dump({"model": model, "features": features}, ruta_modelo)
    print(f"💾 Modelo guardado en: {ruta_modelo}")

if __name__ == "__main__":
    entrenar_modelo_demanda()