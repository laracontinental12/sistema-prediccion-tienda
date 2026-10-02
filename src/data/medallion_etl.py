import pandas as pd
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.services.supabase_client import get_supabase

def transformar_bronze_a_silver():
    supabase = get_supabase()
    
    # 1. Leer datos crudos de la Capa Bronce
    response = supabase.table("bronze_ventas").select("*").execute()
    data = response.data
    
    if not data:
        print("⚠️ No se encontraron datos en 'bronze_ventas'.")
        return

    df = pd.DataFrame(data)
    
    # 2. Transformaciones y Feature Engineering
    df['fecha'] = pd.to_datetime(df['fecha'])
    df['ingreso_total'] = df['unidades_vendidas'] * df['precio_venta']
    df['dia_semana'] = df['fecha'].dt.weekday
    df['es_fin_semana'] = df['dia_semana'].apply(lambda x: 1 if x >= 5 else 0)
    df['fecha'] = df['fecha'].dt.strftime('%Y-%m-%d')
    
    # Seleccionar columnas relevantes para Silver
    columnas_silver = [
        "fecha", "producto_id", "unidades_vendidas", 
        "precio_venta", "ingreso_total", "flag_promocion", 
        "stock_disponible", "dia_semana", "es_fin_semana"
    ]
    df_silver = df[columnas_silver]
    
    # 3. Cargar datos transformados en la Capa Plata
    supabase.table("silver_ventas").delete().neq("id", 0).execute()
    registros = df_silver.to_dict(orient="records")
    supabase.table("silver_ventas").insert(registros).execute()
    
    print(f"✨ Capa Plata actualizada con éxito: {len(registros)} registros procesados.")

if __name__ == "__main__":
    transformar_bronze_a_silver()

# generación tabla gold

import pandas as pd
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.services.supabase_client import get_supabase

def transformar_bronze_a_silver():
    supabase = get_supabase()
    response = supabase.table("bronze_ventas").select("*").execute()
    data = response.data
    
    if not data:
        print("⚠️ No se encontraron datos en 'bronze_ventas'.")
        return

    df = pd.DataFrame(data)
    df['fecha'] = pd.to_datetime(df['fecha'])
    df['ingreso_total'] = df['unidades_vendidas'] * df['precio_venta']
    df['dia_semana'] = df['fecha'].dt.weekday
    df['es_fin_semana'] = df['dia_semana'].apply(lambda x: 1 if x >= 5 else 0)
    df['fecha'] = df['fecha'].dt.strftime('%Y-%m-%d')
    
    columnas_silver = [
        "fecha", "producto_id", "unidades_vendidas", 
        "precio_venta", "ingreso_total", "flag_promocion", 
        "stock_disponible", "dia_semana", "es_fin_semana"
    ]
    df_silver = df[columnas_silver]
    
    supabase.table("silver_ventas").delete().neq("id", 0).execute()
    registros = df_silver.to_dict(orient="records")
    supabase.table("silver_ventas").insert(registros).execute()
    print(f"✨ Capa Plata actualizada con éxito: {len(registros)} registros procesados.")
    return df_silver

def transformar_silver_a_gold():
    supabase = get_supabase()
    response = supabase.table("silver_ventas").select("*").execute()
    data = response.data
    
    if not data:
        print("⚠️ No se encontraron datos en 'silver_ventas'.")
        return

    df = pd.DataFrame(data)
    
    # Agrupación y métricas clave para la Capa Oro
    df_gold = df.groupby(["fecha", "producto_id"]).agg(
        total_unidades=("unidades_vendidas", "sum"),
        total_ingresos=("ingreso_total", "sum"),
        promedio_precio=("precio_venta", "mean"),
        dias_con_promocion=("flag_promocion", "max")
    ).reset_index()
    
    supabase.table("gold_ventas_diarias").delete().neq("id", 0).execute()
    registros = df_gold.to_dict(orient="records")
    supabase.table("gold_ventas_diarias").insert(registros).execute()
    print(f"🥇 Capa Oro actualizada con éxito: {len(registros)} registros consolidados.")

if __name__ == "__main__":
    transformar_bronze_a_silver()
    transformar_silver_a_gold()