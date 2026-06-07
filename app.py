import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Dashboard RCN ASTRANS",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Dashboard Financiero y Operativo RCN ASTRANS")

archivo = st.file_uploader("Carga el archivo Excel", type=["xlsx"])

if archivo is None:
    st.info("Carga un archivo Excel para iniciar.")
    st.stop()

df = pd.read_excel(archivo)

df.columns = (
    df.columns.astype(str)
    .str.strip()
    .str.upper()
    .str.replace(".", "_", regex=False)
    .str.replace(" ", "_", regex=False)
)

df = df.rename(columns={
    "V_CLIENTE": "VALOR_CLIENTE",
    "T_NEGOCIO": "TIPO_NEGOCIO",
    "T_VEHICULO": "TIPO_VEHICULO"
})

columnas = ["AÑO", "MES", "VALOR_CLIENTE", "TIPO_NEGOCIO", "TIPO_VEHICULO"]

faltantes = [c for c in columnas if c not in df.columns]

if faltantes:
    st.error(f"Faltan estas columnas: {faltantes}")
    st.stop()

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

f_anio = st.sidebar.multiselect(
    "Año",
    sorted(df["AÑO"].unique()),
    default=sorted(df["AÑO"].unique())
)

f_negocio = st.sidebar.multiselect(
    "Tipo de negocio",
    sorted(df["TIPO_NEGOCIO"].dropna().unique()),
    default=sorted(df["TIPO_NEGOCIO"].dropna().unique())
)

f_vehiculo = st.sidebar.multiselect(
    "Tipo de vehículo",
    sorted(df["TIPO_VEHICULO"].dropna().unique()),
    default=sorted(df["TIPO_VEHICULO"].dropna().unique())
)

df_f = df[
    (df["AÑO"].isin(f_anio)) &
    (df["TIPO_NEGOCIO"].isin(f_negocio)) &
    (df["TIPO_VEHICULO"].isin(f_vehiculo))
]

ingresos = df_f["VALOR_CLIENTE"].sum()
servicios = len(df_f)
ticket = ingresos / servicios if servicios > 0 else 0

resumen = (
    df_f.groupby(["FECHA", "AÑO_MES"], as_index=False)
    .agg(
        INGRESOS=("VALOR_CLIENTE", "sum"),
        SERVICIOS=("VALOR_CLIENTE", "count")
    )
    .sort_values("FECHA")
)

resumen["VARIACION_%"] = resumen["INGRESOS"].pct_change() * 100
resumen["TICKET_PROMEDIO"] = resumen["INGRESOS"] / resumen["SERVICIOS"]

k1, k2, k3, k4 = st.columns(4)

k1.metric("Ingresos totales", f"${ingresos:,.0f}")
k2.metric("Servicios", f"{servicios:,.0f}")
k3.metric("Ticket promedio", f"${ticket:,.0f}")

if len(resumen) > 1:
    k4.metric("Variación último mes", f"{resumen['VARIACION_%'].iloc[-1]:,.2f}%")
else:
    k4.metric("Variación último mes", "N/A")

st.divider()

c1, c2 = st.columns(2)

with c1:
    st.subheader("Ingresos mensuales")
    fig = px.bar(resumen, x="AÑO_MES", y="INGRESOS", text_auto=True)
    st.plotly_chart(fig, use_container_width=True)

with c2:
    st.subheader("Servicios mensuales")
    fig = px.line(resumen, x="AÑO_MES", y="SERVICIOS", markers=True)
    st.plotly_chart(fig, use_container_width=True)

c3, c4 = st.columns(2)

with c3:
    st.subheader("Participación por tipo de negocio")
    negocio = (
        df_f.groupby("TIPO_NEGOCIO", as_index=False)
        .agg(INGRESOS=("VALOR_CLIENTE", "sum"))
    )
    fig = px.pie(negocio, names="TIPO_NEGOCIO", values="INGRESOS", hole=0.45)
    st.plotly_chart(fig, use_container_width=True)

with c4:
    st.subheader("Ingresos por tipo de vehículo")
    vehiculo = (
        df_f.groupby("TIPO_VEHICULO", as_index=False)
        .agg(INGRESOS=("VALOR_CLIENTE", "sum"))
        .sort_values("INGRESOS", ascending=False)
    )
    fig = px.bar(vehiculo, x="INGRESOS", y="TIPO_VEHICULO", orientation="h", text_auto=True)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

st.subheader("Resumen mensual")

tabla = resumen.copy()
tabla["INGRESOS"] = tabla["INGRESOS"].map("${:,.0f}".format)
tabla["TICKET_PROMEDIO"] = tabla["TICKET_PROMEDIO"].map("${:,.0f}".format)
tabla["VARIACION_%"] = tabla["VARIACION_%"].fillna(0).map("{:,.2f}%".format)

st.dataframe(
    tabla[["AÑO_MES", "INGRESOS", "SERVICIOS", "TICKET_PROMEDIO", "VARIACION_%"]],
    use_container_width=True
)

st.divider()

st.subheader("Análisis cualitativo automático")

if not resumen.empty:
    mes_mayor = resumen.loc[resumen["INGRESOS"].idxmax()]
    mes_menor = resumen.loc[resumen["INGRESOS"].idxmin()]

    st.write(f"""
    La operación registra ingresos acumulados por **${ingresos:,.0f}**, 
    con **{servicios:,.0f} servicios ejecutados** y un ticket promedio de **${ticket:,.0f}**.

    El mes con mayor ingreso fue **{mes_mayor['AÑO_MES']}**, con **${mes_mayor['INGRESOS']:,.0f}**.
    El mes con menor ingreso fue **{mes_menor['AÑO_MES']}**, con **${mes_menor['INGRESOS']:,.0f}**.

    La lectura gerencial permite evaluar crecimiento, participación por línea de negocio 
    y concentración operativa por tipo de vehículo.
    """)

st.divider()

st.subheader("Base filtrada")
st.dataframe(df_f, use_container_width=True)
