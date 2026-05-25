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
.block-container {{ padding-top: 1rem; }}
h1, h2, h3 {{ color: {AZUL}; }}
[data-testid="stMetric"] {{
    background: white;
    border: 1px solid #D8E2EE;
    border-radius: 14px;
    padding: 14px;
    box-shadow: 0 2px 8px rgba(18,58,99,0.08);
}}
</style>
""", unsafe_allow_html=True)

st.title("🚐 Simulador mensual conductor + vehículo 14x7")
st.caption("Transporte especial empresarial | Control semanal legal + costo mensual empresa + neto conductor")

MESES = {"Enero": 1, "Febrero": 2, "Marzo": 3, "Abril": 4, "Mayo": 5, "Junio": 6, "Julio": 7, "Agosto": 8, "Septiembre": 9, "Octubre": 10, "Noviembre": 11, "Diciembre": 12}
DIAS_SEMANA = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

def cop(valor):
    return f"${round(float(valor)):,}".replace(",", ".")

def hrs(valor):
    return f"{round(float(valor), 1):,.1f} h".replace(",", ".")

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

def construir_programacion(anio, mes, dia_inicio_ciclo, hora_inicio, hora_fin, festivos_manual):
    dias_mes = calendar.monthrange(anio, mes)[1]
    horas_dia, _, _ = rango_horas(hora_inicio, hora_fin)
    noct_dia = horas_nocturnas_turno(hora_inicio, hora_fin)
    diur_dia = max(0, horas_dia - noct_dia)
    filas = []
    festivos_asignados = 0
    for d in range(1, dias_mes + 1):
        f = date(anio, mes, d)
        semana_mes = ((d - 1) // 7) + 1
        dia_ciclo = ((dia_inicio_ciclo + d - 2) % 21) + 1
        trabaja = dia_ciclo <= 14
        domingo = f.weekday() == 6
        festivo = False
        if trabaja and not domingo and festivos_asignados < festivos_manual:
            festivo = True
            festivos_asignados += 1
        horas_totales = horas_dia if trabaja else 0
        horas_noct = noct_dia if trabaja else 0
        horas_diur = diur_dia if trabaja else 0
        if not trabaja:
            etiqueta = "DESCANSO"
        elif festivo:
            etiqueta = "FESTIVO"
        elif domingo:
            etiqueta = "DOMINICAL"
        elif horas_noct > 0:
            etiqueta = "LABORA / NOCT."
        else:
            etiqueta = "LABORA"
        filas.append({
            "Fecha": f, "Día": d, "Semana": semana_mes, "Día semana": DIAS_SEMANA[f.weekday()],
            "Día ciclo 14x7": dia_ciclo, "Estado": "LABORA" if trabaja else "DESCANSO", "Etiqueta": etiqueta,
            "Es dominical": domingo, "Dominical laborado": trabaja and domingo,
            "Festivo laborado": festivo, "Horas totales": horas_totales,
            "Horas diurnas reales": horas_diur, "Horas nocturnas reales": horas_noct
        })
    return pd.DataFrame(filas)

with st.sidebar:
    st.header("⚙️ Parámetros")
    anio = st.number_input("Año", min_value=2025, max_value=2035, value=2026)
    mes_nombre = st.selectbox("Mes", list(MESES.keys()), index=4)
    mes = MESES[mes_nombre]
    cantidad_conductores = st.number_input("Cantidad de conductores", min_value=1, max_value=500, value=1)

    st.divider(); st.subheader("📅 Programación automática 14x7")
    dia_inicio_ciclo = st.slider("Día del ciclo 14x7 al iniciar el mes", 1, 21, 1)
    hora_inicio = st.time_input("Hora inicio", value=time(3, 0), step=1800)
    hora_fin = st.time_input("Hora finalización", value=time(16, 0), step=1800)
    horas_ley_semana = st.number_input("Horas legales semanales", min_value=1.0, max_value=60.0, value=45.0, step=1.0)
    max_disponibles = st.number_input("Máximo recomendado horas disponibles", min_value=1.0, max_value=24.0, value=12.0, step=0.5)
    limite_fatiga = st.number_input("Límite máximo fatiga", min_value=1.0, max_value=24.0, value=15.0, step=0.5)
    festivos_laborados_simulados = st.number_input("Festivos laborados simulados", min_value=0, max_value=10, value=0)

    st.divider(); st.subheader("💰 Conductor")
    smlv = st.number_input("SMLV / salario base", min_value=0, value=1750905, step=10000)
    bono_disp = st.number_input("Bono disponibilidad", min_value=0, value=214000, step=10000)
    bono_res = st.number_input("Bono resultados", min_value=0, value=240492, step=10000)
    bono_com = st.number_input("Bono comunicación", min_value=0, value=30000, step=5000)

    st.divider(); st.subheader("📌 Recargos")
    rec_nocturno = st.number_input("Recargo nocturno %", 0.0, 200.0, 35.0, step=1.0) / 100
    rec_extra_diurna = st.number_input("Extra diurna %", 0.0, 200.0, 25.0, step=1.0) / 100
    rec_extra_nocturna = st.number_input("Extra nocturna %", 0.0, 200.0, 75.0, step=1.0) / 100
    rec_dominical = st.number_input("Dominical %", 0.0, 200.0, tarifa_dom(anio)*100, step=1.0) / 100
    rec_festivo = st.number_input("Festivo %", 0.0, 200.0, tarifa_dom(anio)*100, step=1.0) / 100

    st.divider(); st.subheader("🧾 Prestaciones y aportes empresa")
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
    fsp_pct = st.number_input("FSP %", 0.0, 10.0, 0.0, step=0.01) / 100

    st.divider(); st.subheader("💳 Descuentos conductor")
    salud_trab_pct = st.number_input("Salud empleado %", 0.0, 20.0, 4.0, step=0.1) / 100
    pension_trab_pct = st.number_input("Pensión empleado %", 0.0, 20.0, 4.0, step=0.1) / 100
    otros_descuentos = st.number_input("Otros descuentos", min_value=0, value=0, step=10000)

    st.divider(); st.subheader("🚐 Costos vehículo")
    soat = st.number_input("SOAT mensualizado", min_value=0, value=0, step=10000)
    tecnomecanica = st.number_input("Técnico-mecánica mensualizada", min_value=0, value=0, step=10000)
    polizas = st.number_input("Pólizas / seguros operación", min_value=0, value=0, step=10000)
    gps = st.number_input("GPS / plataforma monitoreo", min_value=0, value=0, step=10000)
    administracion = st.number_input("Administración / documentación", min_value=0, value=0, step=10000)
    dotacion = st.number_input("Dotación", min_value=0, value=0, step=10000)
    alimentacion = st.number_input("Alimentación", min_value=0, value=0, step=10000)
    lavado = st.number_input("Lavado general vehículo", min_value=0, value=0, step=10000)
    estadia = st.number_input("Estadía", min_value=0, value=0, step=10000)
    peaje = st.number_input("Peaje con chip", min_value=0, value=0, step=10000)
    combustible = st.number_input("Combustible", min_value=0, value=0, step=10000)
    parqueadero = st.number_input("Parqueadero", min_value=0, value=0, step=10000)
    mantenimiento = st.number_input("Mantenimiento", min_value=0, value=0, step=10000)

    st.divider(); st.subheader("🎯 Productividad")
    produccion = st.number_input("Producción vehículo", min_value=0, value=16000000, step=100000)
    meta_produccion = st.number_input("Meta mínima productividad", min_value=0, value=16000000, step=100000)
    pct_comision = st.slider("% comisión productividad", 0.0, 10.0, 2.0, 0.5) / 100

# Cálculos operacionales
df = construir_programacion(anio, mes, dia_inicio_ciclo, hora_inicio, hora_fin, int(festivos_laborados_simulados))
horas_dia, _, _ = rango_horas(hora_inicio, hora_fin)
total_horas = df["Horas totales"].sum()
horas_nocturnas = df["Horas nocturnas reales"].sum()
horas_diurnas = df["Horas diurnas reales"].sum()
dias_laborados = int((df["Estado"] == "LABORA").sum())
dias_descanso = int((df["Estado"] == "DESCANSO").sum())
domingos_laborados = int(df["Dominical laborado"].sum())
domingos_no_laborados = int(((df["Es dominical"] == True) & (df["Estado"] == "DESCANSO")).sum())
festivos_laborados = int(df["Festivo laborado"].sum())
festivos_no_laborados = max(0, int(festivos_laborados_simulados) - festivos_laborados)

weekly_rows = []
for semana, gp in df.groupby("Semana"):
    ht = gp["Horas totales"].sum()
    hn = gp["Horas nocturnas reales"].sum()
    hd = gp["Horas diurnas reales"].sum()
    base_semana = min(ht, horas_ley_semana)
    exceso_semana = max(0, ht - horas_ley_semana)
    faltante_semana = max(0, horas_ley_semana - ht)
    extras_nocturnas_sem = min(hn, exceso_semana)
    extras_diurnas_sem = max(0, exceso_semana - extras_nocturnas_sem)
    weekly_rows.append({
        "Semana": f"Semana {semana}", "Días laborados": int((gp["Estado"] == "LABORA").sum()),
        "Días descanso": int((gp["Estado"] == "DESCANSO").sum()), "Horas totales": ht,
        "Horas base semana": base_semana, "Faltante semanal": faltante_semana,
        "Exceso sobre 45h": exceso_semana, "Horas diurnas": hd, "Horas nocturnas": hn,
        "Extras diurnas": extras_diurnas_sem, "Extras nocturnas": extras_nocturnas_sem,
        "Domingos laborados": int(gp["Dominical laborado"].sum()), "Festivos laborados": int(gp["Festivo laborado"].sum())
    })
weekly_df = pd.DataFrame(weekly_rows)
horas_base_totales = weekly_df["Horas base semana"].sum()
horas_faltantes_totales = weekly_df["Faltante semanal"].sum()
horas_exceso_totales = weekly_df["Exceso sobre 45h"].sum()
horas_extras_diurnas = weekly_df["Extras diurnas"].sum()
horas_extras_nocturnas = weekly_df["Extras nocturnas"].sum()

# Cálculos financieros
base_salarial = smlv + bono_res + bono_disp
valor_hora = base_salarial / 220 if base_salarial else 0
valor_nocturno = horas_nocturnas * valor_hora * rec_nocturno
valor_extra_diurna = horas_extras_diurnas * valor_hora * (1 + rec_extra_diurna)
valor_extra_nocturna = horas_extras_nocturnas * valor_hora * (1 + rec_extra_nocturna)
valor_dominical = domingos_laborados * horas_dia * valor_hora * rec_dominical
valor_festivo = festivos_laborados * horas_dia * valor_hora * rec_festivo
total_recargos = valor_nocturno + valor_extra_diurna + valor_extra_nocturna + valor_dominical + valor_festivo
comision = produccion * pct_comision if produccion >= meta_produccion else 0
devengado = smlv + bono_disp + bono_res + bono_com + total_recargos + comision
prima = base_salarial * prima_pct
ces = base_salarial * ces_pct
int_ces = base_salarial * int_ces_pct
vac = base_salarial * vac_pct
total_prestaciones = prima + ces + int_ces + vac
pension_emp = base_salarial * pension_emp_pct
ccp = base_salarial * ccp_pct
arl = base_salarial * arl_pct
salud_emp = base_salarial * salud_emp_pct
sena = base_salarial * sena_pct
icbf = base_salarial * icbf_pct
fsp = base_salarial * fsp_pct
total_aportes = pension_emp + ccp + arl + salud_emp + sena + icbf + fsp
desc_salud = base_salarial * salud_trab_pct
desc_pension = base_salarial * pension_trab_pct
total_descuentos = desc_salud + desc_pension + otros_descuentos
neto_conductor = devengado - total_descuentos
costo_documental = soat + tecnomecanica + polizas + gps + administracion
costo_operativo_vehiculo = dotacion + alimentacion + lavado + estadia + peaje + combustible + parqueadero + mantenimiento
costo_vehiculo = costo_documental + costo_operativo_vehiculo
costo_conductor_empresa = devengado + total_prestaciones + total_aportes
costo_conductor_vehiculo = costo_conductor_empresa + costo_vehiculo
costo_mensual_flota = costo_conductor_vehiculo * cantidad_conductores
ratio_empresa_neto = costo_conductor_vehiculo / neto_conductor if neto_conductor else 0

# Presentación
st.subheader("1️⃣ Totales mensuales principales")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Costo conductor empresa", cop(costo_conductor_empresa))
c2.metric("Costo vehículo", cop(costo_vehiculo))
c3.metric("Conductor + vehículo", cop(costo_conductor_vehiculo))
c4.metric("Neto conductor", cop(neto_conductor))
c5, c6, c7, c8 = st.columns(4)
c5.metric("Costo mensual flota", cop(costo_mensual_flota))
c6.metric("Base salarial", cop(base_salarial))
c7.metric("Empresa paga por $1 neto", f"${ratio_empresa_neto:.2f}")
c8.metric("Comisión productividad", cop(comision))

st.subheader("2️⃣ Totales operacionales del mes")
o1, o2, o3, o4 = st.columns(4)
o1.metric("Días laborados", dias_laborados)
o2.metric("Días descanso", dias_descanso)
o3.metric("Domingos laborados / no", f"{domingos_laborados} / {domingos_no_laborados}")
o4.metric("Festivos laborados / no", f"{festivos_laborados} / {festivos_no_laborados}")
o5, o6, o7, o8 = st.columns(4)
o5.metric("Horas totales", hrs(total_horas))
o6.metric("Horas base semanales", hrs(horas_base_totales))
o7.metric("Exceso sobre 45h", hrs(horas_exceso_totales))
o8.metric("Faltante semanal acumulado", hrs(horas_faltantes_totales))
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
st.subheader("3️⃣ Resumen semanal legal")
weekly_total = weekly_df.copy()
totales = {}
for col in weekly_total.columns:
    if col == "Semana":
        totales[col] = "TOTAL"
    elif pd.api.types.is_numeric_dtype(weekly_total[col]):
        totales[col] = weekly_total[col].sum()
    else:
        totales[col] = ""
weekly_total = pd.concat([weekly_total, pd.DataFrame([totales])], ignore_index=True)
st.dataframe(weekly_total, use_container_width=True, hide_index=True)
st.bar_chart(weekly_df.set_index("Semana")[["Horas totales", "Horas base semana", "Exceso sobre 45h", "Faltante semanal"]])

st.divider()
st.subheader("4️⃣ Horas del mes")
horas_df = pd.DataFrame({"Tipo": ["Horas totales", "Horas base reconocidas por semana", "Exceso sobre 45h", "Faltante semanal acumulado", "Horas diurnas", "Horas nocturnas", "Extras diurnas", "Extras nocturnas"], "Horas": [total_horas, horas_base_totales, horas_exceso_totales, horas_faltantes_totales, horas_diurnas, horas_nocturnas, horas_extras_diurnas, horas_extras_nocturnas]})
st.dataframe(horas_df, use_container_width=True, hide_index=True)
st.bar_chart(horas_df.set_index("Tipo"))

st.divider()
st.subheader("5️⃣ Valores para pagar al conductor")
conductor_df = pd.DataFrame({
    "Concepto": ["SMLV / salario base", "Bono disponibilidad", "Bono resultados", "Bono comunicación", "Recargo nocturno", "Horas extras diurnas", "Horas extras nocturnas", "Dominicales", "Festivos", "Comisión productividad", "Descuento salud empleado", "Descuento pensión empleado", "Otros descuentos", "NETO A PAGAR"],
    "% aplicado": ["", "", "", "", f"{rec_nocturno*100:.0f}%", f"{rec_extra_diurna*100:.0f}%", f"{rec_extra_nocturna*100:.0f}%", f"{rec_dominical*100:.0f}%", f"{rec_festivo*100:.0f}%", f"{pct_comision*100:.1f}%" if produccion >= meta_produccion else "0%", f"{salud_trab_pct*100:.0f}%", f"{pension_trab_pct*100:.0f}%", "", ""],
    "Soporte": ["", "", "", "", hrs(horas_nocturnas), hrs(horas_extras_diurnas), hrs(horas_extras_nocturnas), f"{domingos_laborados} domingos", f"{festivos_laborados} festivos", f"Producción {cop(produccion)} / Meta {cop(meta_produccion)}", cop(base_salarial), cop(base_salarial), "", ""],
    "Valor": [smlv, bono_disp, bono_res, bono_com, valor_nocturno, valor_extra_diurna, valor_extra_nocturna, valor_dominical, valor_festivo, comision, -desc_salud, -desc_pension, -otros_descuentos, neto_conductor]
})
conductor_show = conductor_df.copy(); conductor_show["Valor"] = conductor_show["Valor"].map(cop)
st.dataframe(conductor_show, use_container_width=True, hide_index=True)

st.divider()
st.subheader("6️⃣ Valores que asume la empresa")
empresa_df = pd.DataFrame({
    "Bloque": ["CONDUCTOR", "CONDUCTOR", "CONDUCTOR", "PRESTACIONES", "PRESTACIONES", "PRESTACIONES", "PRESTACIONES", "APORTES", "APORTES", "APORTES", "APORTES", "APORTES", "APORTES", "APORTES", "VEHÍCULO DOCUMENTAL", "VEHÍCULO DOCUMENTAL", "VEHÍCULO DOCUMENTAL", "VEHÍCULO DOCUMENTAL", "VEHÍCULO DOCUMENTAL", "VEHÍCULO OPERATIVO", "VEHÍCULO OPERATIVO", "VEHÍCULO OPERATIVO", "VEHÍCULO OPERATIVO", "VEHÍCULO OPERATIVO", "VEHÍCULO OPERATIVO", "VEHÍCULO OPERATIVO", "VEHÍCULO OPERATIVO", "TOTAL"],
    "Concepto": ["Devengado conductor", "Base salarial", "Total recargos y adicionales", "Prima", "Cesantías", "Interés cesantías", "Vacaciones", "Pensión empresa", "CCP / Caja", "ARL", "Salud empresa", "SENA", "ICBF", "FSP", "SOAT mensualizado", "Técnico-mecánica mensualizada", "Pólizas / seguros", "GPS / plataforma", "Administración documental", "Dotación", "Alimentación", "Lavado general", "Estadía", "Peaje con chip", "Combustible", "Parqueadero", "Mantenimiento", "COSTO CONDUCTOR + VEHÍCULO"],
    "% aplicado": ["", "", "", f"{prima_pct*100:.2f}%", f"{ces_pct*100:.2f}%", f"{int_ces_pct*100:.2f}%", f"{vac_pct*100:.2f}%", f"{pension_emp_pct*100:.2f}%", f"{ccp_pct*100:.2f}%", f"{arl_pct*100:.2f}%", f"{salud_emp_pct*100:.2f}%", f"{sena_pct*100:.2f}%", f"{icbf_pct*100:.2f}%", f"{fsp_pct*100:.2f}%", "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    "Base": ["", cop(base_salarial), "", cop(base_salarial), cop(base_salarial), cop(base_salarial), cop(base_salarial), cop(base_salarial), cop(base_salarial), cop(base_salarial), cop(base_salarial), cop(base_salarial), cop(base_salarial), cop(base_salarial), "", "", "", "", "", "", "", "", "", "", "", "", "", ""],
    "Valor": [devengado, base_salarial, total_recargos, prima, ces, int_ces, vac, pension_emp, ccp, arl, salud_emp, sena, icbf, fsp, soat, tecnomecanica, polizas, gps, administracion, dotacion, alimentacion, lavado, estadia, peaje, combustible, parqueadero, mantenimiento, costo_conductor_vehiculo]
})
empresa_show = empresa_df.copy(); empresa_show["Valor"] = empresa_show["Valor"].map(cop)
st.dataframe(empresa_show, use_container_width=True, hide_index=True)
st.bar_chart(empresa_df[empresa_df["Bloque"] != "TOTAL"].groupby("Bloque")["Valor"].sum())

st.divider()
st.subheader("7️⃣ Programación visual 14x7")
html = "<table style='width:100%; border-collapse:separate; border-spacing:6px;'>"
for semana in sorted(df["Semana"].unique()):
    html += "<tr>"
    for _, r in df[df["Semana"] == semana].iterrows():
        if r["Estado"] == "DESCANSO": bg = "#D9D9D9"
        elif r["Festivo laborado"]: bg = "#CFE2F3"
        elif r["Dominical laborado"]: bg = "#F4CCCC"
        elif r["Horas nocturnas reales"] > 0: bg = "#D9D2E9"
        else: bg = "#D9EAD3"
        cell = f"<div style='font-weight:700;font-size:15px'>{int(r['Día'])}</div><div>{r['Día semana']}</div><div style='font-size:12px'>{r['Estado']}</div><div style='font-size:11px'>D {round(r['Horas diurnas reales'])}h / N {round(r['Horas nocturnas reales'])}h</div>"
        html += f"<td style='background:{bg}; padding:9px; border-radius:10px; text-align:center; border:1px solid #E2E8F0;'>{cell}</td>"
    html += "</tr>"
html += "</table>"
st.markdown(html, unsafe_allow_html=True)
st.caption("Verde: labora | Gris: descanso | Morado: nocturno | Rojo: dominical | Azul: festivo")

st.divider()
st.subheader("8️⃣ Detalle diario descargable")
detalle = df.copy()
detalle["Horas totales"] = detalle["Horas totales"].round(1)
detalle["Horas diurnas reales"] = detalle["Horas diurnas reales"].round(1)
detalle["Horas nocturnas reales"] = detalle["Horas nocturnas reales"].round(1)
st.dataframe(detalle, use_container_width=True, hide_index=True)
st.download_button("⬇️ Descargar detalle diario CSV", data=detalle.to_csv(index=False).encode("utf-8-sig"), file_name=f"detalle_diario_{mes_nombre}_{anio}.csv", mime="text/csv")
