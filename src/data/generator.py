import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Permitir importación de módulos desde src
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.services.supabase_client import get_supabase

def generar_datos_sinteticos(dias=90):
    """
    Genera un dataset sintético para tiendas de conveniencia,
    lo guarda en un archivo CSV local para EDA y lo sube a la Capa Bronce en Supabase.
    """
    # Definición de Catálogo de Productos y Período
    productos = [
        {"id": "PROD_BEBIDA_01", "nombre": "Inca Kola 500ml", "precio": 3.50, "base": 25},
        {"id": "PROD_SNACK_02", "nombre": "Papas Lays 160g", "precio": 5.00, "base": 18},
        {"id": "PROD_ABARROTE_03", "nombre": "Leche Gloria 1L", "precio": 4.80, "base": 15},
        {"id": "PROD_BEBIDA_04", "nombre": "Agua San Mateo 600ml", "precio": 2.20, "base": 30},
        {"id": "PROD_SNACK_05", "nombre": "Galletas Soda Field", "precio": 2.00, "base": 20}
    ]
    
    fecha_inicio = datetime.now() - timedelta(days=dias)
    registros = []

    # Simulación de Comportamiento de Mercado
    for prod in productos:
        for i in range(dias):
            fecha = fecha_inicio + timedelta(days=i)
            es_fin_semana = 1 if fecha.weekday() >= 5 else 0
            promocion = np.random.choice([0, 1], p=[0.85, 0.15])
            
            # Efecto de fin de semana y promociones sobre las ventas
            variacion_aleatoria = np.random.randint(-4, 5)
            ventas = prod["base"] + (8 * es_fin_semana) + (12 * promocion) + variacion_aleatoria
            ventas = max(0, int(ventas))
            
            stock = np.random.randint(15, 60)

            registros.append({
                "fecha": fecha.strftime("%Y-%m-%d"),
                "producto_id": prod["id"],
                "unidades_vendidas": ventas,
                "precio_venta": prod["precio"],
                "flag_promocion": promocion,
                "stock_disponible": stock
            })

    # Convertir a DataFrame
    df = pd.DataFrame(registros)

    # 1. GUARDAR CSV LOCAL
    os.makedirs("data/raw", exist_ok=True)
    ruta_csv = "data/raw/ventas_sinteticas.csv"
    df.to_csv(ruta_csv, index=False, encoding="utf-8")
    print(f"📁 Archivo local generado exitosamente en: {ruta_csv}")

    # 2. CARGAR EN SUPABASE (CAPA BRONCE)
    supabase = get_supabase()
    
    # Limpiar tabla bronce previa para evitar duplicados en pruebas
    supabase.table("bronze_ventas").delete().neq("id", 0).execute()
    
    # Inserción por lotes
    data_dict = df.to_dict(orient="records")
    supabase.table("bronze_ventas").insert(data_dict).execute()
    print(f"✅ {len(data_dict)} registros insertados en la tabla 'bronze_ventas' de Supabase.")

if __name__ == "__main__":
    generar_datos_sinteticos()