import streamlit as st
import pandas as pd
import plotly.express as px
import joblib

st.set_page_config(
    page_title="Dashboard Tortillería", 
    layout="wide"
)

# data
 
@st.cache_data
def cargar_datos():
    df = pd.read_csv("data_synthetic.csv")

    # Variable principal del proyecto
    df["demanda_neta"] = df["entrega"] - df["devolucion"]

    return df


df = cargar_datos()

# modelo

@st.cache_resource
def cargar_modelo():
    modelo = joblib.load("best_model_random_forest.pkl")
    return modelo


modelo = cargar_modelo()


#----- Barra ñateral de seleccion y filtros -----------------------------------

st.sidebar.title("Tortillería")

pagina = st.sidebar.radio(
    "Selecciona una sección",
    [
        "Resumen",
        "Historial",
        "Estimador",
        "Datos"
    ]
)

st.sidebar.markdown("---")
st.sidebar.subheader("Filtros")

# Filtros
años = sorted(df["año"].unique())
meses = sorted(df["mes"].unique())
clientes = sorted(df["cliente_id"].unique())
repartidores = sorted(df["repartidor_id"].unique())

año_seleccionado = st.sidebar.selectbox("Año", ["Todos"] + años)
mes_seleccionado = st.sidebar.selectbox("Mes", ["Todos"] + meses)
cliente_seleccionado = st.sidebar.selectbox("Cliente", ["Todos"] + clientes)
repartidor_seleccionado = st.sidebar.selectbox("Repartidor", ["Todos"] + repartidores)


df_filtrado = df.copy()

if año_seleccionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["año"] == año_seleccionado]

if mes_seleccionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["mes"] == mes_seleccionado]

if cliente_seleccionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["cliente_id"] == cliente_seleccionado]

if repartidor_seleccionado != "Todos":
    df_filtrado = df_filtrado[df_filtrado["repartidor_id"] == repartidor_seleccionado]


#-------- Función de KPIs -----------------------------------------------------

def mostrar_kpis(data):
    total_entregado = data["entrega"].sum()
    total_devuelto = data["devolucion"].sum()
    demanda_neta = data["demanda_neta"].sum()

    if total_entregado > 0:
        porcentaje_devolucion = (total_devuelto / total_entregado) * 100
    else:
        porcentaje_devolucion = 0

    # Promedio diario real: primero suma por día, luego promedia
    demanda_diaria = (
        data.groupby(["año", "mes", "dia_mes"], as_index=False)["demanda_neta"]
        .sum()
    )

    if len(demanda_diaria) > 0:
        promedio_diario = demanda_diaria["demanda_neta"].mean()
    else:
        promedio_diario = 0

    col1, col2, col3, col4, col5 = st.columns(5)

    col1.metric("Kg entregados", f"{total_entregado:,.1f}")
    col2.metric("Kg devueltos", f"{total_devuelto:,.1f}")
    col3.metric("Demanda neta", f"{demanda_neta:,.1f}")
    col4.metric("% devolución", f"{porcentaje_devolucion:.2f}%")
    col5.metric("Promedio diario", f"{promedio_diario:.2f} kg")



#---------------- Pagina 1: Resumen -------------------------
if pagina == "Resumen":
    st.title("Resumen general del negocio")
    st.write("Vista rápida de entregas, devoluciones y demanda neta.")

    mostrar_kpis(df_filtrado)

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        demanda_por_mes = (
            df_filtrado.groupby("mes", as_index=False)["demanda_neta"]
            .sum()
        )

        fig = px.bar(
            demanda_por_mes,
            x="mes",
            y="demanda_neta",
            title="Demanda neta por mes",
            labels={
                "mes": "Mes",
                "demanda_neta": "Demanda neta (kg)"
            }
        )

        st.plotly_chart(fig, use_container_width=True)

    with col2:
        devolucion_por_mes = (
            df_filtrado.groupby("mes", as_index=False)["devolucion"]
            .sum()
        )

        fig = px.bar(
            devolucion_por_mes,
            x="mes",
            y="devolucion",
            title="Devoluciones por mes",
            labels={
                "mes": "Mes",
                "devolución": "Devolución (kg)"
            }
        )

        st.plotly_chart(fig, use_container_width=True)



#--------------- Pagina 2: Historial --------------------------------------

elif pagina == "Historial":
    st.title("Historial de ventas y devoluciones")
    st.write("Comportamiento histórico del negocio.")

    mostrar_kpis(df_filtrado)

    st.markdown("---")

    demanda_anual = (
        df_filtrado.groupby("año", as_index=False)[["entrega", "devolucion", "demanda_neta"]]
        .sum()
    )

    fig_anual = px.line(
        demanda_anual,
        x="año",
        y="demanda_neta",
        markers=True,
        title="Demanda neta por año",
        labels={
            "año": "Año",
            "demanda_neta": "Demanda neta (kg)"
        }
    )

    st.plotly_chart(fig_anual, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        fig_entrega_dev = px.bar(
            demanda_anual,
            x="año",
            y=["entrega", "devolucion"],
            barmode="group",
            title="Entregas vs devoluciones por año",
            labels={
                "value": "Kg",
                "año": "Año",
                "variable": "Variable"
            }
        )

        st.plotly_chart(fig_entrega_dev, use_container_width=True)

    with col2:
        demanda_anual["porcentaje_devolucion"] = (
            demanda_anual["devolucion"] / demanda_anual["entrega"]
        ) * 100

        fig_tasa = px.bar(
            demanda_anual,
            x="año",
            y="porcentaje_devolucion",
            title="Porcentaje de devolución por año",
            labels={
                "año": "Año",
                "porcentaje_devolucion": "% devolución"
            }
        )

        st.plotly_chart(fig_tasa, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        demanda_dia_sem = (
            df_filtrado.groupby("dia_sem", as_index=False)["demanda_neta"]
            .mean()
        )

        fig_dia = px.bar(
            demanda_dia_sem,
            x="dia_sem",
            y="demanda_neta",
            title="Demanda promedio por día de la semana",
            labels={
                "dia_sem": "Día de la semana",
                "demanda_neta": "Demanda promedio (kg)"
            }
        )

        st.plotly_chart(fig_dia, use_container_width=True)

    with col4:
        devolucion_dia_sem = (
            df_filtrado.groupby("dia_sem", as_index=False)["devolucion"]
            .mean()
        )

        fig_dev_dia = px.bar(
            devolucion_dia_sem,
            x="dia_sem",
            y="devolucion",
            title="Devolución promedio por día de la semana",
            labels={
                "dia_sem": "Día de la semana",
                "devolución": "Devolución promedio (kg)"
            }
        )

        st.plotly_chart(fig_dev_dia, use_container_width=True)

    col5, col6 = st.columns(2)

    with col5:
        demanda_mes = (
            df_filtrado.groupby("mes", as_index=False)["demanda_neta"]
            .mean()
        )

        fig_mes = px.bar(
            demanda_mes,
            x="mes",
            y="demanda_neta",
            title="Demanda promedio por mes",
            labels={
                "mes": "Mes",
                "demanda_neta": "Demanda promedio (kg)"
            }
        )

        st.plotly_chart(fig_mes, use_container_width=True)

    with col6:
        demanda_estacion = (
            df_filtrado.groupby("estacion", as_index=False)["demanda_neta"]
            .mean()
        )

        fig_estacion = px.bar(
            demanda_estacion,
            x="estacion",
            y="demanda_neta",
            title="Demanda promedio por estación",
            labels={
                "estacion": "Estación",
                "demanda_neta": "Demanda promedio (kg)"
            }
        )

        st.plotly_chart(fig_estacion, use_container_width=True)


#-------------- Pagina 4: Estimador ---------------------------------------------

elif pagina == "Estimador":
    st.title("Estimador de demanda neta")
    st.write(
        "Esta sección estima la demanda neta esperada y recomienda una producción "
        "ajustada según la prioridad del negocio."
    )

    st.markdown("---")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Datos de entrada")

        cliente_input = st.selectbox(
            "Cliente",
            sorted(df["cliente_id"].unique())
        )

        repartidor_input = st.selectbox(
            "Repartidor",
            sorted(df["repartidor_id"].unique())
        )

        año_input = st.number_input(
            "Año",
            min_value=int(df["año"].min()),
            max_value=2030,
            value=int(df["año"].max())
        )

        mes_input = st.selectbox(
            "Mes",
            sorted(df["mes"].unique())
        )

        dia_mes_input = st.slider(
            "Día del mes",
            min_value=1,
            max_value=31,
            value=15
        )

        dia_sem_input = st.selectbox(
            "Día de la semana",
            sorted(df["dia_sem"].unique())
        )

        estacion_input = st.selectbox(
            "Estación",
            sorted(df["estacion"].unique())
        )



    with col2:
        st.subheader("Configuración de producción")

        modo = st.radio(
            "Modo de producción",
            [
                "Reducir desperdicio",
                "Balanceado",
                "Evitar faltantes"
            ]
        )

        if modo == "Reducir desperdicio":
            margen = 0.00
        elif modo == "Balanceado":
            margen = 0.03
        else:
            margen = 0.07

        st.info(f"Margen aplicado: {margen * 100:.1f}%")

    # dataframe para predicción

    datos_prediccion = pd.DataFrame({
    "cliente_id": [cliente_input],
    "repartidor_id": [repartidor_input],
    "mes": [mes_input],
    "estacion": [estacion_input],
    "año": [año_input],
    "dia_mes": [dia_mes_input],
    "dia_sem": [dia_sem_input]
    })

    st.markdown("---")

    if st.button("Estimar demanda"):
        prediccion = modelo.predict(datos_prediccion)[0]

        if prediccion < 0:
            prediccion = 0

        produccion_recomendada = prediccion * (1 + margen)

        col_a, col_b, col_c = st.columns(3)

        col_a.metric(
            "Demanda neta estimada",
            f"{prediccion:.2f} kg"
        )

        col_b.metric(
            "Producción recomendada",
            f"{produccion_recomendada:.2f} kg"
        )

        col_c.metric(
            "Modo seleccionado",
            modo
        )

        st.success(
            "Estimación generada correctamente. La producción recomendada se calculó "
            "a partir de la demanda neta estimada y el margen seleccionado."
        )

        st.subheader("Datos usados para la predicción")
        st.dataframe(datos_prediccion, use_container_width=True)


#------------------------ Pagina 5: datos ----------------------------------
elif pagina == "Datos":
    st.title("Datos filtrados")
    st.write("Vista previa de los datos utilizados en el dashboard.")

    mostrar_kpis(df_filtrado)

    st.markdown("---")

    st.dataframe(df_filtrado, use_container_width=True)

    st.download_button(
        label="Descargar datos filtrados",
        data=df_filtrado.to_csv(index=False).encode("utf-8"),
        file_name="datos_filtrados.csv",
        mime="text/csv"
    )