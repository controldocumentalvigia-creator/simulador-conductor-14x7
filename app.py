import streamlit as st
import pandas as pd
from datetime import time

st.set_page_config(page_title="Simulador 14x7", layout="wide")

st.title("🚐 Simulador costo conductor + vehículo 14x7")

def cop(valor):
    return f"${valor:,.0f}".replace(",", ".")

with st.sidebar:

    st.header("⚙️ Configuración")

    smlv = st.number_input("SMLV", value=1750905)

    bono_disp = st.number_input("Bono disponibilidad", value=214000)

    bono_res = st.number_input("Bono resultados", value=240492)

    bono_com = st.number_input("Bono comunicación", value=30000)

    transporte = st.number_input("Auxilio / transporte", value=0)

    st.divider()

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

    st.divider()

    produccion = st.number_input(
        "Producción vehículo",
        value=16000000
    )

    porcentaje_comision = st.slider(
        "% comisión productividad",
        0.0,
        10.0,
        2.0
    )

    comision = produccion * (porcentaje_comision / 100)

    st.divider()

    dotacion = st.number_input("Dotación", value=0)

    alimentacion = st.number_input("Alimentación", value=0)

    lavado = st.number_input("Lavado vehículo", value=0)

    estadia = st.number_input("Estadía", value=0)

    peajes = st.number_input("Peajes", value=0)

    combustible = st.number_input("Combustible", value=0)

    parqueadero = st.number_input("Parqueadero", value=0)

    mantenimiento = st.number_input("Mantenimiento", value=0)

base_salarial = smlv + bono_disp + bono_res

valor_hora = base_salarial / 220

horas_nocturnas = 72
horas_diurnas = 216
extras_diurnas = 84
extras_nocturnas = 8
dominicales = 4
festivos = 2

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

prima = base_salarial * 0.0833

cesantias = base_salarial * 0.0833

intereses = base_salarial * 0.01

vacaciones = base_salarial * 0.0417

prestaciones = (
    prima
    + cesantias
    + intereses
    + vacaciones
)

pension_empresa = base_salarial * 0.12

ccp = base_salarial * 0.04

arl = base_salarial * 0.0696

salud_empresa = base_salarial * 0.085

seguridad = (
    pension_empresa
    + ccp
    + arl
    + salud_empresa
)

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

salud_empleado = base_salarial * 0.04

pension_empleado = base_salarial * 0.04

descuentos = salud_empleado + pension_empleado

devengado = (
    smlv
    + bono_disp
    + bono_res
    + bono_com
    + transporte
    + total_recargos
    + comision
)

neto = devengado - descuentos

costo_empresa = (
    devengado
    + prestaciones
    + seguridad
    + costos_vehiculo
)

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Costo empresa",
    cop(costo_empresa)
)

col2.metric(
    "Neto conductor",
    cop(neto)
)

col3.metric(
    "Costos vehículo",
    cop(costos_vehiculo)
)

col4.metric(
    "Comisión productividad",
    cop(comision)
)

st.divider()

detalle = pd.DataFrame({

    "Concepto": [

        "SMLV",
        "Bono disponibilidad",
        "Bono resultados",
        "Bono comunicación",
        "Comisión productividad",
        "Recargos",
        "Prestaciones",
        "Seguridad social",
        "Costos vehículo",
        "NETO CONDUCTOR",
        "COSTO EMPRESA"

    ],

    "Valor": [

        smlv,
        bono_disp,
        bono_res,
        bono_com,
        comision,
        total_recargos,
        prestaciones,
        seguridad,
        costos_vehiculo,
        neto,
        costo_empresa

    ]

})

detalle["Valor"] = detalle["Valor"].apply(cop)

st.dataframe(
    detalle,
    use_container_width=True,
    hide_index=True
)

st.success("✅ Simulador operativo cargado correctamente.")
