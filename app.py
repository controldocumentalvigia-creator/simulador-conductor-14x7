import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(
    page_title="Dashboard RCN ASTRANS",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Dashboard Financiero y Operativo RCN ASTRANS")
st.caption("Análisis de ingresos, producción, participación y variación mensual")

archivo = st.file_uploader("Carga la base Excel", type=["xlsx"])

if archivo is not None:
    df = pd.read_excel(archivo)

    # Limpieza de columnas
    df.columns = (
        df.columns.astype(str)
        .str.strip()
        .str.upper()
        .str.replace(".", "_", regex=False)
        .str.replace(" ", "_", regex=False)
    )

    # Renombrar columnas esperadas
    posibles_columnas = {
        "V_CLIENTE": "VALOR_CLIENTE",
        "VALOR_CLIENTE": "VALOR_CLIENTE",
        "T_NEGOCIO": "TIPO_NEGOCIO",
        "TIPO_NEGOCIO": "TIPO_NEGOCIO",
        "T_VEHICULO": "TIPO_VEHICULO",
        "TIPO_VEHICULO": "TIPO_VEHICULO"
    }

    df = df.rename(columns={c: posibles_columnas[c] for c in df.columns if c in posibles_columnas})

    columnas_requeridas = ["AÑO", "MES", "VALOR_CLIENTE", "TIPO_NEGOCIO", "TIPO_VEHICULO"]

    faltantes = [c for c in columnas_requeridas if c not in df.columns]

    if faltantes:
        st.error(f"Faltan columnas obligatorias: {faltantes}")
        st.stop()

    # Limpieza de valor cliente
    df["VALOR_CLIENTE"] = (
        df["VALOR_CLIENTE"]
        .astype(str)
        .str.replace("$", "", regex=False)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.strip()
    )

    df["VALOR_CLIENTE"] = pd.to_numeric(df["VALOR_CLIENTE"], errors="coerce").fillna(0)

    df["AÑO"] = pd.to_numeric(df["AÑO"], errors="coerce")
    df["MES"] = pd.to_numeric(df["MES"], errors="coerce")

    df = df.dropna(subset=["AÑO", "MES"])
    df["AÑO"] = df["AÑO"].astype(int)
    df["MES"] = df["MES"].astype(int)

    df["FECHA"] = pd.to_datetime(
        dict(year=df["AÑO"], month=df["MES"], day=1),
        errors="coerce"
    )

    df = df.dropna(subset=["FECHA"])

    df["AÑO_MES"] = df["FECHA"].dt.strftime("%Y-%m")

    st.sidebar.header("Filtros")

    anios = st.sidebar.multiselect(
        "Año",
        sorted(df["AÑO"].unique()),
        default=sorted(df["AÑO"].unique())
    )

    negocio = st.sidebar.multiselect(
        "Tipo de negocio",
        sorted(df["TIPO_NEGOCIO"].dropna().unique()),
        default=sorted(df["TIPO_NEGOCIO"].dropna().unique())
    )

    vehiculo = st.sidebar.multiselect(
        "Tipo de vehículo",
        sorted(df["TIPO_VEHICULO"].dropna().unique()),
        default=sorted(df["TIPO_VEHICULO"].dropna().unique())
    )

    df_filtrado = df[
        (df["AÑO"].isin(anios)) &
        (df["TIPO_NEGOCIO"].isin(negocio)) &
        (df["TIPO_VEHICULO"].isin(vehiculo))
    ]

    ingresos = df_filtrado["VALOR_CLIENTE"].sum()
    servicios = len(df_filtrado)
    ticket = ingresos / servicios if servicios > 0 else 0

    resumen_mes = (
        df_filtrado
        .groupby(["FECHA", "AÑO_MES"], as_index=False)
        .agg(
            INGRESOS=("VALOR_CLIENTE", "sum"),
            SERVICIOS=("VALOR_CLIENTE", "count")
        )
        .sort_values("FECHA")
    )

    resumen_mes["VARIACION_%"] = resumen_mes["INGRESOS"].pct_change() * 100
    resumen_mes["TICKET_PROMEDIO"] = resumen_mes["INGRESOS"] / resumen_mes["SERVICIOS"]

    col1, col2, col3, col4 = st.columns(4)

    col1.metric("Ingresos totales", f"${ingresos:,.0f}")
    col2.metric("Servicios", f"{servicios:,.0f}")
    col3.metric("Ticket promedio", f"${ticket:,.0f}")

    if len(resumen_mes) > 1:
        variacion_actual = resumen_mes["VARIACION_%"].iloc[-1]
        col4.metric("Variación último mes", f"{variacion_actual:,.2f}%")
    else:
        col4.metric("Variación último mes", "N/A")

    st.divider()

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Ingresos por mes")
        fig_ingresos = px.bar(
            resumen_mes,
            x="AÑO_MES",
            y="INGRESOS",
            text_auto=True
        )
        fig_ingresos.update_layout(xaxis_title="Mes", yaxis_title="Ingresos")
        st.plotly_chart(fig_ingresos, use_container_width=True)

    with c2:
        st.subheader("Servicios por mes")
        fig_servicios = px.line(
            resumen_mes,
            x="AÑO_MES",
            y="SERVICIOS",
            markers=True
        )
        fig_servicios.update_layout(xaxis_title="Mes", yaxis_title="Servicios")
        st.plotly_chart(fig_servicios, use_container_width=True)

    c3, c4 = st.columns(2)

    with c3:
        st.subheader("Participación por tipo de negocio")
        negocio_df = (
            df_filtrado
            .groupby("TIPO_NEGOCIO", as_index=False)
            .agg(INGRESOS=("VALOR_CLIENTE", "sum"))
        )
        negocio_df["PARTICIPACION_%"] = negocio_df["INGRESOS"] / negocio_df["INGRESOS"].sum() * 100

        fig_negocio = px.pie(
            negocio_df,
            names="TIPO_NEGOCIO",
            values="INGRESOS",
            hole=0.4
        )
        st.plotly_chart(fig_negocio, use_container_width=True)

    with c4:
        st.subheader("Ingresos por tipo de vehículo")
        vehiculo_df = (
            df_filtrado
            .groupby("TIPO_VEHICULO", as_index=False)
            .agg(INGRESOS=("VALOR_CLIENTE", "sum"))
            .sort_values("INGRESOS", ascending=False)
        )

        fig_vehiculo = px.bar(
            vehiculo_df,
            x="INGRESOS",
            y="TIPO_VEHICULO",
            orientation="h",
            text_auto=True
        )
        fig_vehiculo.update_layout(xaxis_title="Ingresos", yaxis_title="Tipo de vehículo")
        st.plotly_chart(fig_vehiculo, use_container_width=True)

    st.divider()

    st.subheader("Resumen mensual financiero y operativo")

    tabla = resumen_mes.copy()
    tabla["INGRESOS"] = tabla["INGRESOS"].map("${:,.0f}".format)
    tabla["TICKET_PROMEDIO"] = tabla["TICKET_PROMEDIO"].map("${:,.0f}".format)
    tabla["VARIACION_%"] = tabla["VARIACION_%"].fillna(0).map("{:,.2f}%".format)

    st.dataframe(
        tabla[["AÑO_MES", "INGRESOS", "SERVICIOS", "TICKET_PROMEDIO", "VARIACION_%"]],
        use_container_width=True
    )

    st.divider()

    st.subheader("Análisis cualitativo automático")

    if not resumen_mes.empty:
        mes_mayor = resumen_mes.loc[resumen_mes["INGRESOS"].idxmax()]
        mes_menor = resumen_mes.loc[resumen_mes["INGRESOS"].idxmin()]

        st.write(
            f"""
            Durante el periodo analizado, la operación registra ingresos acumulados por 
            **${ingresos:,.0f}**, con un total de **{servicios:,.0f} servicios ejecutados** 
            y un ticket promedio de **${ticket:,.0f}**.

            El mes con mayor ingreso fue **{mes_mayor['AÑO_MES']}**, con 
            **${mes_mayor['INGRESOS']:,.0f}**, mientras que el mes de menor ingreso fue 
            **{mes_menor['AÑO_MES']}**, con **${mes_menor['INGRESOS']:,.0f}**.

            La lectura gerencial indica que el comportamiento financiero debe evaluarse 
            en conjunto con la producción operativa, debido a que un mayor número de servicios 
            no siempre garantiza mejor rentabilidad si el ticket promedio disminuye.
            """
        )

        if len(resumen_mes) > 1:
            ultima_var = resumen_mes["VARIACION_%"].iloc[-1]

            if ultima_var > 0:
                st.success(
                    f"La operación presenta crecimiento en el último mes evaluado, con una variación positiva de {ultima_var:,.2f}%."
                )
            elif ultima_var < 0:
                st.warning(
                    f"La operación presenta una disminución en el último mes evaluado, con una variación de {ultima_var:,.2f}%. Se recomienda revisar causas comerciales, operativas o de facturación."
                )
            else:
                st.info("La operación se mantiene estable frente al mes anterior.")

    st.divider()

    st.subheader("Base cargada")
    st.dataframe(df_filtrado, use_container_width=True)

else:
    st.info("Carga el archivo Excel para iniciar el análisis.")
