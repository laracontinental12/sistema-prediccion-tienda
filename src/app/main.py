import streamlit as st
import pandas as pd
import numpy as np
import joblib
import sys
import os

# Permitir importaciones relativas desde la raíz del proyecto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from src.services.supabase_client import get_supabase

# Configuración de página
st.set_page_config(
    page_title="Predicción de Demanda - Tienda de Conveniencia",
    page_icon="🏪",
    layout="wide"
)

st.title("🏪 Sistema de Predicción de Demanda de Ventas")
st.write("Panel de control interactivo conectado a la arquitectura Medallion en Supabase.")

# Cargar artefacto del modelo ML
@st.cache_resource
def cargar_modelo():
    ruta_modelo = "src/models/modelo_prediccion_demanda.pkl"
    if os.path.exists(ruta_modelo):
        return joblib.load(ruta_modelo)
    return None

artefacto_ml = cargar_modelo()

# Navegación
pestana1, pestana2 = st.tabs(["📊 Visualización de Datos (Gold Layer)", "🔮 Realizar Predicción"])

# TAB 1: VISUALIZACIÓN DE DATOS
with pestana1:
    st.header("Datos Consolidados (Capa Oro)")
    
    @st.cache_data(ttl=60)
    def obtener_datos_gold():
        supabase = get_supabase()
        response = supabase.table("gold_ventas_diarias").select("*").execute()
        return pd.DataFrame(response.data)

    try:
        df_gold = obtener_datos_gold()
        if not df_gold.empty:
            # Métricas rápidas
            col1, col2, col3 = st.columns(3)
            col1.metric("Ventas Totales (Unidades)", f"{int(df_gold['total_unidades'].sum()):,}")
            col2.metric("Ingresos Totales ($)", f"${df_gold['total_ingresos'].sum():,.2f}")
            col3.metric("Productos Registrados", len(df_gold['producto_id'].unique()))

            st.subheader("Histórico de Ventas por Producto")
            st.dataframe(df_gold, use_container_width=True)
            
            # Gráfico de ventas
            st.subheader("Tendencia de Ventas")
            chart_data = df_gold.pivot(index='fecha', columns='producto_id', values='total_unidades')
            st.line_chart(chart_data)
        else:
            st.warning("No se encontraron registros en la Capa Oro.")
    except Exception as e:
        st.error(f"Error al cargar datos de Supabase: {e}")

# TAB 2: PREDICCIÓN CON MACHINE LEARNING
with pestana2:
    st.header("Generar Predicción de Demanda")
    
    if artefacto_ml is None:
        st.error("No se encontró el modelo entrenado. Ejecuta primero `python src/models/train.py`.")
    else:
        model = artefacto_ml["model"]
        features_esperadas = artefacto_ml["features"]
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            producto = st.selectbox(
                "Selecciona el Producto",
                ["PROD_BEBIDA_01", "PROD_SNACK_02", "PROD_ABARROTE_03", "PROD_BEBIDA_04", "PROD_SNACK_05"]
            )
            fecha_pred = st.date_input("Fecha a Predecir")
            
        with col_b:
            precio = st.number_input("Precio de Venta ($)", min_value=0.5, max_value=50.0, value=3.5, step=0.1)
            promocion = st.radio("¿Tendrá Promoción?", options=[0, 1], format_func=lambda x: "Sí" if x == 1 else "No")

        if st.button("🚀 Predecir Demanda"):
            # Extraer características temporales
            fecha_dt = pd.to_datetime(fecha_pred)
            dia_semana = fecha_dt.weekday()
            mes = fecha_dt.month
            dia_mes = fecha_dt.day

            # Construir diccionario base para las columnas esperadas por el modelo
            datos_entrada = {f: 0 for f in features_esperadas}
            
            # Asignar valores
            if "promedio_precio" in datos_entrada:
                datos_entrada["promedio_precio"] = precio
            if "dias_con_promocion" in datos_entrada:
                datos_entrada["dias_con_promocion"] = promocion
            if "dia_semana" in datos_entrada:
                datos_entrada["dia_semana"] = dia_semana
            if "mes" in datos_entrada:
                datos_entrada["mes"] = mes
            if "dia_mes" in datos_entrada:
                datos_entrada["dia_mes"] = dia_mes
                
            col_prod = f"producto_id_{producto}"
            if col_prod in datos_entrada:
                datos_entrada[col_prod] = 1

            # Convertir a DataFrame ordenado por las features esperadas
            df_input = pd.DataFrame([datos_entrada])[features_esperadas]
            
            # Ejecutar inferencia
            prediccion = model.predict(df_input)[0]
            
            st.success(f"📦 **Demanda Estimada:** {int(np.round(prediccion))} unidades para el {fecha_pred.strftime('%d/%m/%Y')}")