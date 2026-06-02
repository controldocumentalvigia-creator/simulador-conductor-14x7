
import calendar
from datetime import date, datetime, time, timedelta

import pandas as pd
import streamlit as st

st.set_page_config(page_title="Simulador 14x7 - Transporte Especial", page_icon="🚐", layout="wide")

AZUL = "#123A63"
FONDO = "#F6F9FC"

st.markdown(f"""
<style>
.stApp {{ background-color: {FONDO}; }}
.block-container {{ padding-top: 1rem; padding-bottom: 2rem; }}
h1, h2, h3 {{ color: {AZUL}; }}
[data-testid="stMetric"] {{
    background: white;
    border: 1px solid #D8E2EE;
    border-radius: 12px;
    padding: 8px 10px;
    box-shadow: 0 2px 6px rgba(18,58,99,0.06);
}}
[data-testid="stMetricLabel"] {{ font-size: 0.78rem; }}
[data-testid="stMetricValue"] {{ font-size: 1.12rem; }}
div[data-testid="stDataFrame"] {{ background: white; border-radius: 12px; }}
</style>
""", unsafe_allow_html=True)

st.title("🚐 Simulador mensual conductor + vehículo 14x7")
st.caption("Transporte especial empresarial | Nómina operativa mensual + base prestacional/IBC corregida")

MESES = {"Enero": 1, "Febrero": 2, "Marzo": 3, "Abril": 4, "Mayo": 5, "Junio": 6,
         "Julio": 7, "Agosto": 8, "Septiembre": 9, "Octubre": 10, "Noviembre": 11, "Diciembre": 12}
DIAS_SEMANA = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]


def cop(valor):
    return f"${round(float(valor)):,}".replace(",", ".")


def hrs(valor):
    return f"{round(float(valor), 1):,.1f} h".replace(",", ".")


def pct(valor):
    return f"{float(valor) * 100:.2f}%".replace(".", ",")


def rango_horas(inicio, fin):
    base = datetime(2026, 1, 1)
    ini = datetime.combine(base, inicio)
    fi = datetime.combine(base, fin)
    if fi <= ini:
        fi += timedelta(days=1)
    return round((fi - ini).total_seconds() / 3600, 2), ini, fi


def horas_nocturnas_turno(inicio, fin):
    _, ini, fi = rango_horas(inicio, fin)
    cursor = ini
    paso = timedelta(minutes=15)
    nocturnas = 0.0
    while cursor < fi:
        sig = min(cursor + paso, fi)
        bloque = (sig - cursor).total_seconds() / 3600
        t = cursor.time()
        if t >= time(19, 0) or t < time(6, 0):
            nocturnas += bloque
        cursor = sig
    return round(nocturnas, 2)


def tarifa_dom(anio):
    if anio >= 2027:
        return 1.00
    if anio == 2026:
        return 0.90
    return 0.80


def construir_programacion(anio, mes, fecha_inicio_ciclo, hora_inicio, hora_fin, festivos_simulados):
    dias_mes = calendar.monthrange(anio, mes)[1]
    horas_dia, _, _ = rango_horas(hora_inicio, hora_fin)
    noct_dia = horas_nocturnas_turno(hora_inicio, hora_fin)
    diur_dia = max(0, horas_dia - noct_dia)
    filas = []
    festivos_asignados = 0

    for d in range(1, dias_mes + 1):
        fecha = date(anio, mes, d)
        semana_mes = ((d - 1) // 7) + 1
        dias_desde_inicio = (fecha - fecha_inicio_ciclo).days
        dia_ciclo = (dias_desde_inicio % 21) + 1
        trabaja = dia_ciclo <= 14
        es_domingo = fecha.weekday() == 6

        festivo_laborado = False
        if trabaja and not es_domingo and festivos_asignados < festivos_simulados:
            festivo_laborado = True
            festivos_asignados += 1

        horas_totales = horas_dia if trabaja else 0
        horas_noct = noct_dia if trabaja else 0
        horas_diur = diur_dia if trabaja else 0

        if not trabaja:
            etiqueta = "DESCANSO"
        elif festivo_laborado:
            etiqueta = "FESTIVO"
        elif es_domingo:
            etiqueta = "DOMINICAL"
        elif horas_noct > 0:
            etiqueta = "LABORA / NOCT."
        else:
            etiqueta = "LABORA"

        filas.append({
            "Fecha": fecha, "Día": d, "Semana": semana_mes, "Día semana": DIAS_SEMANA[fecha.weekday()],
            "Día ciclo 14x7": dia_ciclo, "Estado": "LABORA" if trabaja else "DESCANSO", "Etiqueta": etiqueta,
            "Es domingo": es_domingo, "Dominical laborado": trabaja and es_domingo, "Festivo laborado": festivo_laborado,
            "Horas totales": horas_totales, "Horas diurnas": horas_diur, "Horas nocturnas": horas_noct,
        })
    return pd.DataFrame(filas)


with st.sidebar:
    st.header("⚙️ Parámetros")
    anio = st.number_input("Año", min_value=2025, max_value=2035, value=2026)
    mes_nombre = st.selectbox("Mes", list(MESES.keys()), index=5)
    mes = MESES[mes_nombre]
    cantidad_conductores = st.number_input("Cantidad de conductores", min_value=1, max_value=500, value=1)

    st.divider()
    st.subheader("📅 Programación 14x7")
    fecha_inicio_ciclo = st.date_input("Fecha real de inicio del ciclo 14x7", value=date(2026, 6, 8), help="Desde esta fecha se cuenta: 14 días laborados y 7 días de descanso.")
    hora_inicio = st.time_input("Hora inicio", value=time(3, 0), step=1800)
    hora_fin = st.time_input("Hora finalización", value=time(16, 0), step=1800)
    horas_ley_semana = st.number_input("Referencia legal semanal", min_value=1.0, max_value=60.0, value=45.0, step=1.0)
    horas_base_dia_operacional = st.number_input("Horas base operacionales por día laborado", min_value=1.0, max_value=12.0, value=8.0, step=0.5)
    max_disponibles = st.number_input("Máximo recomendado horas disponibles", min_value=1.0, max_value=24.0, value=12.0, step=0.5)
    limite_fatiga = st.number_input("Límite máximo fatiga", min_value=1.0, max_value=24.0, value=15.0, step=0.5)
    festivos_laborados_simulados = st.number_input("Festivos laborados simulados", min_value=0, max_value=10, value=0)

    st.divider()
    st.subheader("💰 Conductor")
    smlv = st.number_input("SMLV / salario base", min_value=0, value=1750905, step=10000)
    bono_disp = st.number_input("Bono disponibilidad", min_value=0, value=214000, step=10000)
    bono_res = st.number_input("Bono resultados", min_value=0, value=240492, step=10000)
    bono_com = st.number_input("Bono comunicación / auxilio no prestacional", min_value=0, value=30000, step=5000)

    st.markdown("**🎯 Productividad**")
    produccion = st.number_input("Producción vehículo", min_value=0, value=16000000, step=100000)
    meta_produccion = st.number_input("Meta mínima productividad", min_value=0, value=16000000, step=100000)
    pct_comision_input = st.number_input("% comisión productividad", min_value=0.0, max_value=100.0, value=2.2, step=0.01)
    pct_comision = pct_comision_input / 100

    st.divider()
    st.subheader("📌 Recargos")
    rec_nocturno = st.number_input("Recargo nocturno %", 0.0, 200.0, 35.0, step=1.0) / 100
    rec_extra_diurna = st.number_input("Extra diurna %", 0.0, 200.0, 25.0, step=1.0) / 100
    rec_extra_nocturna = st.number_input("Extra nocturna %", 0.0, 200.0, 75.0, step=1.0) / 100
    rec_dominical = st.number_input("Dominical %", 0.0, 200.0, tarifa_dom(anio) * 100, step=1.0) / 100
    rec_festivo = st.number_input("Festivo %", 0.0, 200.0, tarifa_dom(anio) * 100, step=1.0) / 100

    st.divider()
    st.subheader("🧾 Prestaciones y aportes empresa")
    prima_pct = st.number_input("Prima %", 0.0, 20.0, 8.33, step=0.01) / 100
    ces_pct = st.number_input("Cesantías %", 0.0, 20.0, 8.33, step=0.01) / 100
    int_ces_pct = st.number_input("Interés cesantías %", 0.0, 10.0, 1.0, step=0.01) / 100
    vac_pct = st.number_input("Vacaciones %", 0.0, 20.0, 4.17, step=0.01) / 100
    pension_emp_pct = st.number_input("Pensión empresa %", 0.0, 30.0, 12.0, step=0.01) / 100
    ccp_pct = st.number_input("CCP / Caja %", 0.0, 20.0, 4.0, step=0.01) / 100
    arl_pct = st.number_input("ARL %", 0.0, 20.0, 6.96, step=0.01) / 100
    salud_emp_pct = st.number_input("Salud empresa %", 0.0, 20.0, 8.5, step=0.01) / 100
    sena_pct = st.number_input("SENA %", 0.0, 10.0, 0.0, step=0.01) / 100
    icbf_pct = st.number_input("ICBF %", 0.0, 10.0, 0.0, step=0.01) / 100

    st.divider()
    st.subheader("💳 Descuentos conductor")
    salud_trab_pct = st.number_input("Salud empleado %", 0.0, 20.0, 4.0, step=0.1) / 100
    pension_trab_pct = st.number_input("Pensión empleado %", 0.0, 20.0, 4.0, step=0.1) / 100
    otros_descuentos = st.number_input("Otros descuentos", min_value=0, value=0, step=10000)

    st.divider()
    st.subheader("🚐 Gastos vehículo")
    soat = st.number_input("SOAT mensualizado", min_value=0, value=0, step=10000)
    tecnomecanica = st.number_input("Técnico-mecánica mensualizada", min_value=0, value=0, step=10000)
    polizas = st.number_input("Pólizas / seguros operación", min_value=0, value=0, step=10000)
    gps = st.number_input("GPS / plataforma monitoreo", min_value=0, value=0, step=10000)
    administracion = st.number_input("Administración / documentación", min_value=0, value=0, step=10000)
    lavado = st.number_input("Lavado general vehículo", min_value=0, value=0, step=10000)
    peaje = st.number_input("Peaje con chip", min_value=0, value=0, step=10000)
    combustible = st.number_input("Combustible", min_value=0, value=0, step=10000)
    parqueadero = st.number_input("Parqueadero", min_value=0, value=0, step=10000)
    mantenimiento = st.number_input("Mantenimiento", min_value=0, value=0, step=10000)

    st.divider()
    st.subheader("👤 Gastos conductor")
    dotacion = st.number_input("Dotación", min_value=0, value=0, step=10000)
    alimentacion = st.number_input("Alimentación", min_value=0, value=0, step=10000)
    estadia = st.number_input("Estadía", min_value=0, value=0, step=10000)


df = construir_programacion(anio, mes, fecha_inicio_ciclo, hora_inicio, hora_fin, int(festivos_laborados_simulados))

horas_dia, _, _ = rango_horas(hora_inicio, hora_fin)
total_horas = df["Horas totales"].sum()
horas_nocturnas = df["Horas nocturnas"].sum()
horas_diurnas = df["Horas diurnas"].sum()

dias_laborados = int((df["Estado"] == "LABORA").sum())
dias_descanso = int((df["Estado"] == "DESCANSO").sum())
domingos_laborados = int(df["Dominical laborado"].sum())
domingos_no_laborados = int(((df["Es domingo"] == True) & (df["Estado"] == "DESCANSO")).sum())
festivos_laborados = int(df["Festivo laborado"].sum())
festivos_no_laborados = max(0, int(festivos_laborados_simulados) - festivos_laborados)

horas_base_operacional = dias_laborados * horas_base_dia_operacional
horas_extras_operacionales = max(0, total_horas - horas_base_operacional)
horas_extras_nocturnas = min(horas_nocturnas, horas_extras_operacionales)
horas_extras_diurnas = max(0, horas_extras_operacionales - horas_extras_nocturnas)

weekly_rows = []
for semana, gp in df.groupby("Semana"):
    ht = gp["Horas totales"].sum()
    hn = gp["Horas nocturnas"].sum()
    hd = gp["Horas diurnas"].sum()
    exceso_semana = max(0, ht - horas_ley_semana)
    faltante_semana = max(0, horas_ley_semana - ht)
    weekly_rows.append({
        "Semana": f"Semana {semana}", "Días laborados": int((gp["Estado"] == "LABORA").sum()),
        "Días descanso": int((gp["Estado"] == "DESCANSO").sum()), "Horas totales": ht,
        "Referencia legal semanal": horas_ley_semana, "Exceso legal semanal": exceso_semana,
        "Faltante semanal": faltante_semana, "Horas diurnas": hd, "Horas nocturnas": hn,
        "Domingos laborados": int(gp["Dominical laborado"].sum()), "Festivos laborados": int(gp["Festivo laborado"].sum())
    })
weekly_df = pd.DataFrame(weekly_rows)

# =========================================================
# CÁLCULOS FINANCIEROS
# =========================================================
# Base fija inicial para calcular valor hora.
base_fija_salarial = smlv + bono_disp + bono_res
valor_hora = base_fija_salarial / 220 if base_fija_salarial else 0

valor_nocturno = horas_nocturnas * valor_hora * rec_nocturno
valor_extra_diurna = horas_extras_diurnas * valor_hora * (1 + rec_extra_diurna)
valor_extra_nocturna = horas_extras_nocturnas * valor_hora * (1 + rec_extra_nocturna)
valor_dominical = domingos_laborados * horas_dia * valor_hora * rec_dominical
valor_festivo = festivos_laborados * horas_dia * valor_hora * rec_festivo

total_recargos = valor_nocturno + valor_extra_diurna + valor_extra_nocturna + valor_dominical + valor_festivo
comision = produccion * pct_comision if produccion >= meta_produccion else 0

# Base prestacional / IBC corregida.
base_prestacional_ibc = base_fija_salarial + total_recargos + comision
no_prestacional = bono_com

devengado = base_fija_salarial + bono_com + total_recargos + comision

prima = base_prestacional_ibc * prima_pct
ces = base_prestacional_ibc * ces_pct
int_ces = base_prestacional_ibc * int_ces_pct
vac = base_prestacional_ibc * vac_pct
total_prestaciones = prima + ces + int_ces + vac

pension_emp = base_prestacional_ibc * pension_emp_pct
ccp = base_prestacional_ibc * ccp_pct
arl = base_prestacional_ibc * arl_pct
salud_emp = base_prestacional_ibc * salud_emp_pct
sena = base_prestacional_ibc * sena_pct
icbf = base_prestacional_ibc * icbf_pct
total_aportes = pension_emp + ccp + arl + salud_emp + sena + icbf

desc_salud = base_prestacional_ibc * salud_trab_pct
desc_pension = base_prestacional_ibc * pension_trab_pct
total_descuentos = desc_salud + desc_pension + otros_descuentos
neto_conductor = devengado - total_descuentos

gasto_vehiculo = soat + tecnomecanica + polizas + gps + administracion + lavado + peaje + combustible + parqueadero + mantenimiento
gasto_conductor = dotacion + alimentacion + estadia

costo_conductor_empresa = devengado + total_prestaciones + total_aportes
costo_total_empresa_mensual = costo_conductor_empresa + gasto_vehiculo + gasto_conductor
costo_mensual_flota = costo_total_empresa_mensual * cantidad_conductores

st.subheader("1️⃣ Totales mensuales principales")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total a pagar al conductor", cop(neto_conductor))
c2.metric("Gasto conductor", cop(gasto_conductor))
c3.metric("Gasto vehículo", cop(gasto_vehiculo))
c4.metric("Costo total empresa mensual", cop(costo_total_empresa_mensual))

c5, c6, c7, c8 = st.columns(4)
c5.metric("Costo mensual flota", cop(costo_mensual_flota))
c6.metric("Base prestacional / IBC", cop(base_prestacional_ibc))
c7.metric("Total recargos", cop(total_recargos))
c8.metric("Comisión productividad", cop(comision))

st.subheader("2️⃣ Panel operacional mensual")
o1, o2, o3, o4 = st.columns(4)
o1.metric("Días laborados", dias_laborados)
o2.metric("Días descanso", dias_descanso)
o3.metric("Domingos laborados / no", f"{domingos_laborados} / {domingos_no_laborados}")
o4.metric("Festivos laborados / no", f"{festivos_laborados} / {festivos_no_laborados}")

o5, o6, o7, o8 = st.columns(4)
o5.metric("Horas totales", hrs(total_horas))
o6.metric("Horas base operacionales", hrs(horas_base_operacional))
o7.metric("Extras operacionales", hrs(horas_extras_operacionales))
o8.metric("Horas día", hrs(horas_dia))

o9, o10, o11, o12 = st.columns(4)
o9.metric("Horas diurnas", hrs(horas_diurnas))
o10.metric("Horas nocturnas", hrs(horas_nocturnas))
o11.metric("Extras diurnas", hrs(horas_extras_diurnas))
o12.metric("Extras nocturnas", hrs(horas_extras_nocturnas))

if horas_dia > limite_fatiga:
    st.error(f"🚨 Fatiga crítica: {hrs(horas_dia)} por día supera el límite de {hrs(limite_fatiga)}.")
elif horas_dia > max_disponibles:
    st.warning(f"⚠️ Jornada superior a {hrs(max_disponibles)} disponibles. Validar horas adicionales.")
else:
    st.success("✅ Jornada dentro de parámetros operativos configurados.")

st.divider()
st.subheader("3️⃣ Horas del mes")
horas_df = pd.DataFrame({"Tipo": ["Horas totales", "Horas base operacionales", "Extras operacionales", "Horas diurnas", "Horas nocturnas", "Extras diurnas", "Extras nocturnas"], "Horas": [total_horas, horas_base_operacional, horas_extras_operacionales, horas_diurnas, horas_nocturnas, horas_extras_diurnas, horas_extras_nocturnas]})
st.dataframe(horas_df, use_container_width=True, hide_index=True)

st.divider()
st.subheader("4️⃣ ¿Cuánto se le paga al conductor?")
conductor_df = pd.DataFrame({
    "Concepto": ["SMLV / salario base", "Bono disponibilidad", "Bono resultados", "Bono comunicación no prestacional", "Recargo nocturno", "Extras diurnas", "Extras nocturnas", "Dominicales", "Festivos", "Comisión productividad", "Descuento salud empleado", "Descuento pensión empleado", "Otros descuentos", "NETO A PAGAR A CUENTA BANCARIA"],
    "% aplicado": ["", "", "", "", pct(rec_nocturno), pct(rec_extra_diurna), pct(rec_extra_nocturna), pct(rec_dominical), pct(rec_festivo), f"{pct_comision_input:.2f}%".replace(".", ",") if produccion >= meta_produccion else "0%", pct(salud_trab_pct), pct(pension_trab_pct), "", ""],
    "Soporte": ["", "", "", "No prestacional", hrs(horas_nocturnas), hrs(horas_extras_diurnas), hrs(horas_extras_nocturnas), f"{domingos_laborados} domingos", f"{festivos_laborados} festivos", f"Producción {cop(produccion)} / Meta {cop(meta_produccion)}", cop(base_prestacional_ibc), cop(base_prestacional_ibc), "", ""],
    "Valor": [smlv, bono_disp, bono_res, bono_com, valor_nocturno, valor_extra_diurna, valor_extra_nocturna, valor_dominical, valor_festivo, comision, -desc_salud, -desc_pension, -otros_descuentos, neto_conductor]
})
conductor_show = conductor_df.copy()
conductor_show["Valor"] = conductor_show["Valor"].map(cop)
st.dataframe(conductor_show, use_container_width=True, hide_index=True)

st.divider()
st.subheader("5️⃣ ¿Cuánto paga la empresa por el conductor?")
empresa_conductor_df = pd.DataFrame({
    "Concepto": ["Devengado conductor", "Base fija salarial", "Base prestacional / IBC corregida", "Valor no prestacional", "Prima", "Cesantías", "Interés cesantías", "Vacaciones", "Pensión empresa", "Caja compensación / CCP", "ARL", "Salud empresa", "SENA", "ICBF", "TOTAL COSTO CONDUCTOR EMPRESA"],
    "% aplicado": ["", "", "", "", pct(prima_pct), pct(ces_pct), pct(int_ces_pct), pct(vac_pct), pct(pension_emp_pct), pct(ccp_pct), pct(arl_pct), pct(salud_emp_pct), pct(sena_pct), pct(icbf_pct), ""],
    "Base": ["", cop(base_fija_salarial), cop(base_prestacional_ibc), cop(no_prestacional), cop(base_prestacional_ibc), cop(base_prestacional_ibc), cop(base_prestacional_ibc), cop(base_prestacional_ibc), cop(base_prestacional_ibc), cop(base_prestacional_ibc), cop(base_prestacional_ibc), cop(base_prestacional_ibc), cop(base_prestacional_ibc), cop(base_prestacional_ibc), ""],
    "Valor": [devengado, base_fija_salarial, base_prestacional_ibc, no_prestacional, prima, ces, int_ces, vac, pension_emp, ccp, arl, salud_emp, sena, icbf, costo_conductor_empresa]
})
empresa_conductor_show = empresa_conductor_df.copy()
empresa_conductor_show["Valor"] = empresa_conductor_show["Valor"].map(cop)
st.dataframe(empresa_conductor_show, use_container_width=True, hide_index=True)

st.divider()
st.subheader("6️⃣ Gastos vehículo")
gasto_vehiculo_df = pd.DataFrame({"Concepto": ["SOAT", "Técnico-mecánica", "Pólizas / seguros operación", "GPS / plataforma monitoreo", "Administración / documentación", "Lavado general vehículo", "Peaje con chip", "Combustible", "Parqueadero", "Mantenimiento", "TOTAL GASTO VEHÍCULO"], "Valor": [soat, tecnomecanica, polizas, gps, administracion, lavado, peaje, combustible, parqueadero, mantenimiento, gasto_vehiculo]})
gasto_vehiculo_show = gasto_vehiculo_df.copy()
gasto_vehiculo_show["Valor"] = gasto_vehiculo_show["Valor"].map(cop)
st.dataframe(gasto_vehiculo_show, use_container_width=True, hide_index=True)

st.divider()
st.subheader("7️⃣ Gastos conductor")
gasto_conductor_df = pd.DataFrame({"Concepto": ["Dotación", "Alimentación", "Estadía", "TOTAL GASTOS CONDUCTOR"], "Valor": [dotacion, alimentacion, estadia, gasto_conductor]})
gasto_conductor_show = gasto_conductor_df.copy()
gasto_conductor_show["Valor"] = gasto_conductor_show["Valor"].map(cop)
st.dataframe(gasto_conductor_show, use_container_width=True, hide_index=True)

st.divider()
st.subheader("8️⃣ Panel legal semanal - alerta")
legal_total = weekly_df.copy()
totales = {}
for col in legal_total.columns:
    if col == "Semana":
        totales[col] = "TOTAL"
    elif pd.api.types.is_numeric_dtype(legal_total[col]):
        totales[col] = legal_total[col].sum()
    else:
        totales[col] = ""
legal_total = pd.concat([legal_total, pd.DataFrame([totales])], ignore_index=True)
st.dataframe(legal_total, use_container_width=True, hide_index=True)

l1, l2, l3 = st.columns(3)
l1.metric("Exceso legal semanal acumulado", hrs(weekly_df["Exceso legal semanal"].sum()))
l2.metric("Faltante semanal acumulado", hrs(weekly_df["Faltante semanal"].sum()))
l3.metric("Referencia semanal", hrs(horas_ley_semana))

st.divider()
st.subheader("9️⃣ Programación visual 14x7")
html = "<table style='width:100%; border-collapse:separate; border-spacing:6px;'>"
for semana in sorted(df["Semana"].unique()):
    html += "<tr>"
    for _, r in df[df["Semana"] == semana].iterrows():
        if r["Estado"] == "DESCANSO":
            bg = "#D9D9D9"
        elif r["Festivo laborado"]:
            bg = "#CFE2F3"
        elif r["Dominical laborado"]:
            bg = "#F4CCCC"
        elif r["Horas nocturnas"] > 0:
            bg = "#D9D2E9"
        else:
            bg = "#D9EAD3"
        cell = f"""
        <div style='font-weight:700;font-size:15px'>{int(r['Día'])}</div>
        <div>{r['Día semana']}</div>
        <div style='font-size:12px'>{r['Estado']}</div>
        <div style='font-size:11px'>D {round(r['Horas diurnas'])}h / N {round(r['Horas nocturnas'])}h</div>
        """
        html += f"<td style='background:{bg}; padding:9px; border-radius:10px; text-align:center; border:1px solid #E2E8F0;'>{cell}</td>"
    html += "</tr>"
html += "</table>"
st.markdown(html, unsafe_allow_html=True)
st.caption("Verde: labora | Gris: descanso | Morado: nocturno | Rojo: dominical | Azul: festivo")

st.divider()
st.subheader("🔟 Detalle diario descargable")
detalle = df.copy()
detalle["Horas totales"] = detalle["Horas totales"].round(1)
detalle["Horas diurnas"] = detalle["Horas diurnas"].round(1)
detalle["Horas nocturnas"] = detalle["Horas nocturnas"].round(1)
st.dataframe(detalle, use_container_width=True, hide_index=True)
st.download_button("⬇️ Descargar detalle diario CSV", data=detalle.to_csv(index=False).encode("utf-8-sig"), file_name=f"detalle_diario_{mes_nombre}_{anio}.csv", mime="text/csv")
