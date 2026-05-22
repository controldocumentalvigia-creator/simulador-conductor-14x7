import streamlit as st
import pandas as pd
from datetime import datetime, time

# =========================================================
# CONFIGURACIÓN GENERAL
# =========================================================

st.set_page_config(
    page_title="Dashboard Ejecutivo 14x7",
    page_icon="🚐",
    layout="wide"
)

st.title("🚐 DASHBOARD EJECUTIVO COSTO OPERACIONAL 14x7")
st.caption("Costo real empresa vs neto conductor | Transporte especial y empresarial")

# =========================================================
# FUNCIONES
# =========================================================

def formato_pesos(valor):
    return f"${valor:,.0f}".replace(",", ".")

# =========================================================
# SIDEBAR
# =========================================================

with st.sidebar:

    st.header("⚙️ CONFIGURACIÓN OPERACIONAL")

    # -----------------------------------
    # BASE SALARIAL
    # -----------------------------------

    st.subheader("💰 Base salarial")

    smlv = st.number_input(
        "SMLV",
        value=1750905,
        step=10000
    )

    bono_disponibilidad = st.number_input(
        "Bono disponibilidad",
        value=214000,
        step=10000
    )

    bono_resultados = st.number_input(
        "Bono resultados",
        value=240492,
        step=10000
    )

    bono_comunicacion = st.number_input(
        "Bono comunicación",
        value=30000,
        step=5000
    )

    valor_transporte = st.number_input(
        "Valor transporte",
        value=0,
        step=10000
    )

    # -----------------------------------
    # PROGRAMACIÓN
    # -----------------------------------

    st.divider()

    st.subheader("🕐 Programación")

    hora_inicio = st.time_input(
        "Hora inicio",
        value=time(3,0)
    )

    hora_fin = st.time_input(
        "Hora fin",
        value=time(15,0)
    )

    horas_disponibles = st.slider(
        "Horas disponibles",
        1,
        15,
        12
    )

    limite_fatiga = st.slider(
        "Límite fatiga",
        1,
        24,
        15
    )

    # -----------------------------------
    # PRODUCTIVIDAD
    # -----------------------------------

    st.divider()

    st.subheader("📈 Productividad")

    produccion_vehiculo = st.number_input(
        "Producción vehículo",
        value=16000000,
        step=100000
    )

    meta_productividad = st.number_input(
        "Meta mínima productividad",
        value=16000000,
        step=100000
    )

    porcentaje_comision = st.slider(
        "% comisión productividad",
        0.0,
        10.0,
        2.0
    )

    # -----------------------------------
    # COSTOS VEHÍCULO
    # -----------------------------------

    st.divider()

    st.subheader("🚐 Costos vehículo")

    dotacion = st.number_input("Dotación", value=0)
    alimentacion = st.number_input("Alimentación", value=0)
    lavado = st.number_input("Lavado vehículo", value=0)
    estadia = st.number_input("Estadía", value=0)
    peajes = st.number_input("Peajes", value=0)
    combustible = st.number_input("Combustible", value=0)
    parqueadero = st.number_input("Parqueadero", value=0)
    mantenimiento = st.number_input("Mantenimiento", value=0)

# =========================================================
# BASE SALARIAL
# =========================================================

base_salarial = (
    smlv
    + bono_resultados
    + bono_disponibilidad
)

valor_hora = base_salarial / 220

# =========================================================
# HORAS EJEMPLO OPERACIONAL
# =========================================================

horas_diurnas = 216
horas_nocturnas = 72

extras_diurnas = 84
extras_nocturnas = 8

dominicales = 4
festivos = 2

# =========================================================
# RECARGOS
# =========================================================

recargo_nocturno = horas_nocturnas * valor_hora * 0.35

valor_extra_diurna = extras_diurnas * valor_hora * 1.25

valor_extra_nocturna = extras_nocturnas * valor_hora * 1.75

valor_dominical = dominicales * 12 * valor_hora * 0.80

valor_festivo = festivos * 12 * valor_hora * 0.80

total_recargos = (
    recargo_nocturno
    + valor_extra_diurna
    + valor_extra_nocturna
    + valor_dominical
    + valor_festivo
)

# =========================================================
# COMISIÓN PRODUCTIVIDAD
# =========================================================

if produccion_vehiculo >= meta_productividad:

    comision_productividad = (
        produccion_vehiculo
        * (porcentaje_comision / 100)
    )

else:

    comision_productividad = 0

# =========================================================
# PRESTACIONES
# =========================================================

prima = base_salarial * 0.0833
cesantias = base_salarial * 0.0833
intereses_ces = base_salarial * 0.01
vacaciones = base_salarial * 0.0417

total_prestaciones = (
    prima
    + cesantias
    + intereses_ces
    + vacaciones
)

# =========================================================
# APORTES EMPRESA
# =========================================================

pension_empresa = base_salarial * 0.12
ccp = base_salarial * 0.04
arl = base_salarial * 0.0696

total_aportes_empresa = (
    pension_empresa
    + ccp
    + arl
)

# =========================================================
# PARAFISCALES
# =========================================================

salud_empresa = base_salarial * 0.085
sena = 0
icbf = 0
fsp = 0

total_parafiscales = (
    salud_empresa
    + sena
    + icbf
    + fsp
)

# =========================================================
# DESCUENTOS CONDUCTOR
# =========================================================

salud_conductor = base_salarial * 0.04
pension_conductor = base_salarial * 0.04

total_descuentos = (
    salud_conductor
    + pension_conductor
)

# =========================================================
# DEVENGADO CONDUCTOR
# =========================================================

devengado_conductor = (
    smlv
    + bono_disponibilidad
    + bono_resultados
    + bono_comunicacion
    + valor_transporte
    + total_recargos
    + comision_productividad
)

# =========================================================
# NETO CONDUCTOR
# =========================================================

neto_conductor = (
    devengado_conductor
    - total_descuentos
)

# =========================================================
# COSTOS VEHÍCULO
# =========================================================

costos_vehiculo = (
    dotacion
    + alimentacion
    + lavado
    + estadia
    + peajes
    + combustible
    + parqueadero
    + mantenimiento
)

# =========================================================
# COSTO TOTAL EMPRESA
# =========================================================

costo_empresa = (
    devengado_conductor
    + total_prestaciones
    + total_aportes_empresa
    + total_parafiscales
    + costos_vehiculo
)

# =========================================================
# KPIS
# =========================================================

st.subheader("📌 KPIs Ejecutivos")

k1, k2, k3, k4 = st.columns(4)

k1.metric(
    "Costo total empresa",
    formato_pesos(costo_empresa)
)

k2.metric(
    "Neto conductor",
    formato_pesos(neto_conductor)
)

k3.metric(
    "Costos vehículo",
    formato_pesos(costos_vehiculo)
)

k4.metric(
    "Comisión productividad",
    formato_pesos(comision_productividad)
)

# =========================================================
# ALERTAS
# =========================================================

st.divider()

st.subheader("🚨 Alertas operacionales")

if horas_disponibles > 12:

    st.warning(
        "⚠️ Las horas disponibles superan 12 horas."
    )

if horas_disponibles > limite_fatiga:

    st.error(
        "🚨 Riesgo de fatiga operacional."
    )

else:

    st.success(
        "✅ Jornada dentro del límite de fatiga."
    )

# =========================================================
# TABLA NETO CONDUCTOR
# =========================================================

st.divider()

st.subheader("💳 ¿Qué recibe el conductor?")

tabla_conductor = pd.DataFrame({

    "Concepto": [

        "SMLV",
        "Bono disponibilidad",
        "Bono resultados",
        "Bono comunicación",
        "Recargos",
        "Comisión productividad",
        "Salud conductor",
        "Pensión conductor",
        "NETO CONDUCTOR"

    ],

    "Valor": [

        smlv,
        bono_disponibilidad,
        bono_resultados,
        bono_comunicacion,
        total_recargos,
        comision_productividad,
        -salud_conductor,
        -pension_conductor,
        neto_conductor

    ]

})

tabla_conductor["Valor"] = tabla_conductor["Valor"].apply(
    formato_pesos
)

st.dataframe(
    tabla_conductor,
    use_container_width=True,
    hide_index=True
)

# =========================================================
# TABLA COSTO EMPRESA
# =========================================================

st.divider()

st.subheader("🏢 ¿Qué paga realmente la empresa?")

tabla_empresa = pd.DataFrame({

    "Concepto": [

        "Devengado conductor",
        "Prima 8,33%",
        "Cesantías 8,33%",
        "Intereses cesantías 1%",
        "Vacaciones 4,17%",
        "Pensión empresa 12%",
        "CCP 4%",
        "ARL 6,96%",
        "Salud empresa 8,5%",
        "Costos vehículo",
        "COSTO TOTAL EMPRESA"

    ],

    "Valor": [

        devengado_conductor,
        prima,
        cesantias,
        intereses_ces,
        vacaciones,
        pension_empresa,
        ccp,
        arl,
        salud_empresa,
        costos_vehiculo,
        costo_empresa

    ]

})

tabla_empresa["Valor"] = tabla_empresa["Valor"].apply(
    formato_pesos
)

st.dataframe(
    tabla_empresa,
    use_container_width=True,
    hide_index=True
)

# =========================================================
# HORAS
# =========================================================

st.divider()

st.subheader("⏰ Resumen de horas")

tabla_horas = pd.DataFrame({

    "Tipo": [

        "Horas diurnas",
        "Horas nocturnas",
        "Extras diurnas",
        "Extras nocturnas",
        "Dominicales",
        "Festivos"

    ],

    "Cantidad": [

        horas_diurnas,
        horas_nocturnas,
        extras_diurnas,
        extras_nocturnas,
        dominicales,
        festivos

    ]

})

st.dataframe(
    tabla_horas,
    use_container_width=True,
    hide_index=True
)

st.bar_chart(
    tabla_horas.set_index("Tipo")
)

# =========================================================
# PROGRAMACIÓN 14x7
# =========================================================

st.divider()

st.subheader("📅 Programación visual 14x7")

html = """

<table style='width:100%; border-spacing:10px;'>

<tr>

<td style='background:#D9EAD3;padding:20px;border-radius:10px;'>LABORA</td>
<td style='background:#D9EAD3;padding:20px;border-radius:10px;'>LABORA</td>
<td style='background:#D9EAD3;padding:20px;border-radius:10px;'>LABORA</td>
<td style='background:#D9EAD3;padding:20px;border-radius:10px;'>LABORA</td>
<td style='background:#D9EAD3;padding:20px;border-radius:10px;'>LABORA</td>
<td style='background:#D9EAD3;padding:20px;border-radius:10px;'>LABORA</td>
<td style='background:#F4CCCC;padding:20px;border-radius:10px;'>DOM</td>

</tr>

<tr>

<td style='background:#D9EAD3;padding:20px;border-radius:10px;'>LABORA</td>
<td style='background:#D9EAD3;padding:20px;border-radius:10px;'>LABORA</td>
<td style='background:#D9EAD3;padding:20px;border-radius:10px;'>LABORA</td>
<td style='background:#D9EAD3;padding:20px;border-radius:10px;'>LABORA</td>
<td style='background:#D9EAD3;padding:20px;border-radius:10px;'>LABORA</td>
<td style='background:#CFE2F3;padding:20px;border-radius:10px;'>FEST</td>
<td style='background:#D9EAD3;padding:20px;border-radius:10px;'>LABORA</td>

</tr>

<tr>

<td style='background:#D9D9D9;padding:20px;border-radius:10px;'>DESC</td>
<td style='background:#D9D9D9;padding:20px;border-radius:10px;'>DESC</td>
<td style='background:#D9D9D9;padding:20px;border-radius:10px;'>DESC</td>
<td style='background:#D9D9D9;padding:20px;border-radius:10px;'>DESC</td>
<td style='background:#D9D9D9;padding:20px;border-radius:10px;'>DESC</td>
<td style='background:#D9D9D9;padding:20px;border-radius:10px;'>DESC</td>
<td style='background:#D9D9D9;padding:20px;border-radius:10px;'>DESC</td>

</tr>

</table>

"""

st.markdown(
    html,
    unsafe_allow_html=True
)

# =========================================================
# FINAL
# =========================================================

st.success(
    "✅ Dashboard ejecutivo 14x7 cargado correctamente."
)
