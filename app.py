
import calendar
from datetime import date, datetime, time, timedelta
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Simulador conductor + vehiculo 14x7", page_icon="🚐", layout="wide")

AZUL = "#173B63"; AZUL2 = "#245A8D"; FONDO = "#F6F8FB"; BLANCO = "#FFFFFF"
VERDE = "#D9EAD3"; GRIS = "#E7E9ED"; MORADO = "#DDD6FE"; ROJO = "#F8D7DA"; AZUL_CLARO = "#D9EAF7"

st.markdown(f"""
<style>
.stApp {{ background: {FONDO}; }}
.block-container {{ padding-top: 1.2rem; }}
.main-title {{ background: linear-gradient(90deg, {AZUL}, {AZUL2}); color: white; padding: 22px 28px; border-radius: 18px; box-shadow: 0 6px 18px rgba(23,59,99,.18); }}
.main-title h1 {{ margin: 0; font-size: 34px; }}
.main-title p {{ margin: 6px 0 0 0; opacity: .92; }}
.section-title {{ color: {AZUL}; font-weight: 800; font-size: 24px; margin-top: 14px; }}
[data-testid="stMetric"] {{ background-color: white; border: 1px solid #E2E8F0; padding: 14px; border-radius: 16px; box-shadow: 0 2px 8px rgba(0,0,0,.04); }}
[data-testid="stMetricLabel"] {{ color: {AZUL}; font-weight: 700; }}
[data-testid="stMetricValue"] {{ color: #111827; font-weight: 800; }}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class='main-title'>
<h1>🚐 Simulador ejecutivo conductor + vehículo 14x7</h1>
<p>Transporte especial empresarial | Costo empresa vs neto conductor | Programación, horas, recargos, prestaciones y operación</p>
</div>
""", unsafe_allow_html=True)

def cop(v): return f"${round(float(v)):,}".replace(",", ".")
def hrs(v): return f"{round(float(v)):,} h".replace(",", ".")
def pct(v): return f"{v*100:.2f}%"
def calc_valor_hora(base_salarial): return base_salarial / 220 if base_salarial else 0

def rango_horas(inicio: time, fin: time):
    base = datetime(2026, 1, 1)
    ini = datetime.combine(base, inicio); fi = datetime.combine(base, fin)
    if fi <= ini: fi += timedelta(days=1)
    return (fi - ini).total_seconds() / 3600, ini, fi

def clasificar_bloques(inicio: time, fin: time, horas_ordinarias_dia: float):
    total, ini, fi = rango_horas(inicio, fin)
    cursor = ini; paso = timedelta(minutes=15); acumulado = 0.0
    res = {"ord_dia": 0.0, "ord_noc": 0.0, "ext_dia": 0.0, "ext_noc": 0.0, "dia_total": 0.0, "noc_total": 0.0, "total": total}
    while cursor < fi:
        sig = min(cursor + paso, fi)
        bloque = (sig - cursor).total_seconds() / 3600
        t = cursor.time(); es_noche = t >= time(19, 0) or t < time(6, 0)
        es_extra = acumulado >= horas_ordinarias_dia
        if es_noche:
            res["noc_total"] += bloque
            res["ext_noc" if es_extra else "ord_noc"] += bloque
        else:
            res["dia_total"] += bloque
            res["ext_dia" if es_extra else "ord_dia"] += bloque
        acumulado += bloque; cursor = sig
    return {k: round(v, 2) for k, v in res.items()}

def crear_programacion(anio, mes, dia_ciclo_inicio, hora_inicio, hora_fin, horas_ordinarias_dia, festivos_laborados):
    dias_mes = calendar.monthrange(anio, mes)[1]
    turno = clasificar_bloques(hora_inicio, hora_fin, horas_ordinarias_dia)
    registros = []; festivos_asignados = 0; ciclo = dia_ciclo_inicio
    for d in range(1, dias_mes + 1):
        f = date(anio, mes, d); dia_ciclo = ((ciclo - 1) % 21) + 1
        labora = dia_ciclo <= 14; domingo = f.weekday() == 6
        festivo = False
        if labora and not domingo and festivos_asignados < festivos_laborados:
            festivo = True; festivos_asignados += 1
        if labora:
            ord_dia, ord_noc, ext_dia, ext_noc = turno["ord_dia"], turno["ord_noc"], turno["ext_dia"], turno["ext_noc"]
            dia_total, noc_total, total = turno["dia_total"], turno["noc_total"], turno["total"]
        else:
            ord_dia = ord_noc = ext_dia = ext_noc = dia_total = noc_total = total = 0
        if not labora: etiqueta, color = "DESCANSO", GRIS
        elif festivo: etiqueta, color = "FESTIVO", AZUL_CLARO
        elif domingo: etiqueta, color = "DOMINICAL", ROJO
        elif noc_total > 0: etiqueta, color = "LABORA / NOCT.", MORADO
        else: etiqueta, color = "LABORA", VERDE
        registros.append({"Fecha": f, "Día": d, "Semana": ((d - 1)//7)+1, "Día semana": ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"][f.weekday()], "Día ciclo 14x7": dia_ciclo, "Estado": "LABORA" if labora else "DESCANSO", "Etiqueta": etiqueta, "Color": color, "Es domingo": domingo, "Es festivo": festivo, "Horas totales": total, "Horas diurnas": dia_total, "Horas nocturnas": noc_total, "Ordinarias diurnas": ord_dia, "Ordinarias nocturnas": ord_noc, "Extras diurnas": ext_dia, "Extras nocturnas": ext_noc})
        ciclo += 1
    return pd.DataFrame(registros)

MESES = {"Enero":1,"Febrero":2,"Marzo":3,"Abril":4,"Mayo":5,"Junio":6,"Julio":7,"Agosto":8,"Septiembre":9,"Octubre":10,"Noviembre":11,"Diciembre":12}

with st.sidebar:
    st.markdown(f"<h2 style='color:{AZUL};'>⚙️ Parámetros</h2>", unsafe_allow_html=True)
    anio = st.number_input("Año", 2025, 2035, 2026)
    mes_nombre = st.selectbox("Mes", list(MESES.keys()), index=4); mes = MESES[mes_nombre]
    conductores = st.number_input("Cantidad conductores / vehículos", 1, 500, 1)
    dia_ciclo_inicio = st.slider("Día del ciclo 14x7 al iniciar el mes", 1, 21, 1)
    st.divider(); st.subheader("🕐 Programación")
    hora_inicio = st.time_input("Hora inicio", value=time(3, 0), step=1800)
    hora_fin = st.time_input("Hora finalización", value=time(16, 0), step=1800)
    horas_disponibles = st.number_input("Horas disponibles por día", 1.0, 15.0, 12.0, step=0.5)
    horas_ordinarias_dia = st.number_input("Horas ordinarias base día", 1.0, 12.0, 8.0, step=0.5)
    limite_fatiga = st.number_input("Límite de fatiga", 1.0, 24.0, 15.0, step=0.5)
    festivos_laborados = st.number_input("Festivos laborados en el mes", 0, 10, 0)
    st.divider(); st.subheader("💰 Base salarial / bonos")
    smlv = st.number_input("SMLV / salario base", 0, value=1750905, step=10000)
    bono_disponibilidad = st.number_input("Bono disponibilidad", 0, value=214000, step=10000)
    bono_resultados = st.number_input("Bono resultados", 0, value=240492, step=10000)
    bono_comunicacion = st.number_input("Bono comunicación", 0, value=30000, step=5000)
    valor_transporte = st.number_input("Valor transporte", 0, value=0, step=10000)
    st.divider(); st.subheader("📌 Recargos")
    rec_nocturno = st.number_input("Recargo nocturno %", 0.0, 200.0, 35.0, step=1.0)/100
    rec_extra_diurna = st.number_input("Extra diurna %", 0.0, 200.0, 25.0, step=1.0)/100
    rec_extra_nocturna = st.number_input("Extra nocturna %", 0.0, 200.0, 75.0, step=1.0)/100
    rec_dominical = st.number_input("Dominical %", 0.0, 200.0, 80.0, step=1.0)/100
    rec_festivo = st.number_input("Festivo %", 0.0, 200.0, 80.0, step=1.0)/100
    st.divider(); st.subheader("🧾 Prestaciones / aportes")
    prima_pct = st.number_input("Prima %", 0.0, 20.0, 8.33, step=0.01)/100
    cesantias_pct = st.number_input("Cesantías %", 0.0, 20.0, 8.33, step=0.01)/100
    interes_ces_pct = st.number_input("Intereses cesantías %", 0.0, 10.0, 1.0, step=0.01)/100
    vacaciones_pct = st.number_input("Vacaciones %", 0.0, 20.0, 4.17, step=0.01)/100
    pension_emp_pct = st.number_input("Pensión empresa %", 0.0, 30.0, 12.0, step=0.01)/100
    ccp_pct = st.number_input("CCP / Caja %", 0.0, 20.0, 4.0, step=0.01)/100
    arl_pct = st.number_input("ARL %", 0.0, 20.0, 6.96, step=0.01)/100
    salud_emp_pct = st.number_input("Salud empresa %", 0.0, 20.0, 8.5, step=0.01)/100
    sena_pct = st.number_input("SENA %", 0.0, 10.0, 0.0, step=0.01)/100
    icbf_pct = st.number_input("ICBF %", 0.0, 10.0, 0.0, step=0.01)/100
    fsp_pct = st.number_input("FSP %", 0.0, 10.0, 0.0, step=0.01)/100
    st.divider(); st.subheader("💳 Descuentos conductor")
    salud_cond_pct = st.number_input("Salud empleado %", 0.0, 20.0, 4.0, step=0.1)/100
    pension_cond_pct = st.number_input("Pensión empleado %", 0.0, 20.0, 4.0, step=0.1)/100
    otros_descuentos = st.number_input("Otros descuentos", 0, value=0, step=10000)
    st.divider(); st.subheader("🚐 Costos vehículo")
    dotacion = st.number_input("Dotación", 0, value=0, step=10000)
    alimentacion = st.number_input("Alimentación", 0, value=0, step=10000)
    lavado = st.number_input("Lavado general vehículo", 0, value=0, step=10000)
    estadia = st.number_input("Estadía", 0, value=0, step=10000)
    peaje = st.number_input("Peaje con chip", 0, value=0, step=10000)
    combustible = st.number_input("Combustible", 0, value=0, step=10000)
    parqueadero = st.number_input("Parqueadero", 0, value=0, step=10000)
    mantenimiento = st.number_input("Mantenimiento", 0, value=0, step=10000)
    st.divider(); st.subheader("📈 Productividad")
    produccion = st.number_input("Producción del vehículo", 0, value=16000000, step=100000)
    meta_productividad = st.number_input("Meta mínima productividad", 0, value=16000000, step=100000)
    comision_pct = st.slider("% comisión productividad", 0.0, 10.0, 2.0, 0.5)/100

programacion = crear_programacion(anio, mes, dia_ciclo_inicio, hora_inicio, hora_fin, horas_ordinarias_dia, int(festivos_laborados))
horas_turno, _, _ = rango_horas(hora_inicio, hora_fin)
base_salarial = smlv + bono_resultados + bono_disponibilidad
vh = calc_valor_hora(base_salarial)

num_dias_laborados = int((programacion["Estado"] == "LABORA").sum())
num_descansos = int((programacion["Estado"] == "DESCANSO").sum())
num_domingos = int(((programacion["Estado"] == "LABORA") & (programacion["Es domingo"])).sum())
num_festivos = int(((programacion["Estado"] == "LABORA") & (programacion["Es festivo"])).sum())

h_dia = programacion["Horas diurnas"].sum(); h_noc = programacion["Horas nocturnas"].sum()
h_ord_dia = programacion["Ordinarias diurnas"].sum(); h_ord_noc = programacion["Ordinarias nocturnas"].sum()
h_ext_dia = programacion["Extras diurnas"].sum(); h_ext_noc = programacion["Extras nocturnas"].sum()
h_dom = programacion.loc[(programacion["Estado"]=="LABORA") & (programacion["Es domingo"]), "Horas totales"].sum()
h_fes = programacion.loc[(programacion["Estado"]=="LABORA") & (programacion["Es festivo"]), "Horas totales"].sum()

valor_ord_dia = h_ord_dia * vh; valor_ord_noc_base = h_ord_noc * vh
valor_rec_noc = h_noc * vh * rec_nocturno
valor_ext_dia = h_ext_dia * vh * (1 + rec_extra_diurna)
valor_ext_noc = h_ext_noc * vh * (1 + rec_extra_nocturna)
valor_dom = h_dom * vh * rec_dominical; valor_fes = h_fes * vh * rec_festivo
valor_recargos_total = valor_rec_noc + valor_ext_dia + valor_ext_noc + valor_dom + valor_fes
comision = produccion * comision_pct if produccion >= meta_productividad else 0

prima = base_salarial * prima_pct; cesantias = base_salarial * cesantias_pct
interes_ces = base_salarial * interes_ces_pct; vacaciones = base_salarial * vacaciones_pct
total_prestaciones = prima + cesantias + interes_ces + vacaciones
pension_emp = base_salarial * pension_emp_pct; ccp = base_salarial * ccp_pct; arl = base_salarial * arl_pct
total_aportes = pension_emp + ccp + arl
salud_emp = base_salarial * salud_emp_pct; sena = base_salarial * sena_pct; icbf = base_salarial * icbf_pct; fsp = base_salarial * fsp_pct
total_salud_parafiscales = salud_emp + sena + icbf + fsp
bonos_total = bono_disponibilidad + bono_resultados + bono_comunicacion
devengado_bruto = smlv + bonos_total + valor_transporte + valor_recargos_total + comision
salud_cond = base_salarial * salud_cond_pct; pension_cond = base_salarial * pension_cond_pct
total_descuentos = salud_cond + pension_cond + otros_descuentos
neto_conductor = devengado_bruto - total_descuentos
costo_vehiculo = dotacion + alimentacion + lavado + estadia + peaje + combustible + parqueadero + mantenimiento
costo_conductor = devengado_bruto + total_prestaciones + total_aportes + total_salud_parafiscales
costo_conductor_vehiculo = costo_conductor + costo_vehiculo
costo_flota = costo_conductor_vehiculo * conductores; costo_anual = costo_flota * 12
empresa_por_peso = costo_conductor_vehiculo / neto_conductor if neto_conductor else 0

st.markdown("<div class='section-title'>📌 Resumen ejecutivo</div>", unsafe_allow_html=True)
k1,k2,k3,k4 = st.columns(4)
k1.metric("Costo conductor", cop(costo_conductor)); k2.metric("Costo vehículo", cop(costo_vehiculo)); k3.metric("Conductor + vehículo", cop(costo_conductor_vehiculo)); k4.metric("Neto conductor", cop(neto_conductor))
k5,k6,k7,k8 = st.columns(4)
k5.metric("Costo mensual flota", cop(costo_flota)); k6.metric("Costo anual", cop(costo_anual)); k7.metric("Base salarial", cop(base_salarial)); k8.metric("Empresa paga por cada $1 neto", f"${empresa_por_peso:.2f}")

st.markdown("<div class='section-title'>⏱️ Horas, días y alertas</div>", unsafe_allow_html=True)
h1,h2,h3,h4,h5,h6 = st.columns(6)
h1.metric("Días laborados", num_dias_laborados); h2.metric("Descansos", num_descansos); h3.metric("Domingos", num_domingos); h4.metric("Festivos", num_festivos); h5.metric("Extras", hrs(h_ext_dia + h_ext_noc)); h6.metric("Horas/día", hrs(horas_turno))
h7,h8,h9,h10 = st.columns(4)
h7.metric("Diurnas", hrs(h_dia)); h8.metric("Nocturnas", hrs(h_noc)); h9.metric("Extras diurnas", hrs(h_ext_dia)); h10.metric("Extras nocturnas", hrs(h_ext_noc))

if horas_turno > limite_fatiga: st.error(f"🚨 Fatiga crítica: el turno suma {hrs(horas_turno)} y supera el límite de {hrs(limite_fatiga)}.")
elif horas_turno > 12: st.warning(f"⚠️ Turno superior a 12 horas disponibles: {hrs(horas_turno)}. Validar manejo como adicional/disponibilidad especial.")
else: st.success("✅ Jornada dentro de parámetros operativos configurados.")

st.divider(); st.markdown("<div class='section-title'>💳 Lo que llega al conductor</div>", unsafe_allow_html=True)
conductor_df = pd.DataFrame({"Concepto": ["Salario base", "Bono disponibilidad", "Bono resultados", "Bono comunicación", "Valor transporte", "Recargos / extras / dominicales", "Comisión productividad", "Salud empleado", "Pensión empleado", "Otros descuentos", "NETO A PAGAR"], "% aplicado": ["", "", "", "", "", "Ver detalle recargos", pct(comision_pct) if produccion >= meta_productividad else "No aplica", pct(salud_cond_pct), pct(pension_cond_pct), "", ""], "Base / soporte": ["SMLV", "Editable", "Editable", "Editable", "Editable", "Horas reales del calendario", f"Producción {cop(produccion)} / Meta {cop(meta_productividad)}", cop(base_salarial), cop(base_salarial), "Editable", ""], "Valor": [smlv, bono_disponibilidad, bono_resultados, bono_comunicacion, valor_transporte, valor_recargos_total, comision, -salud_cond, -pension_cond, -otros_descuentos, neto_conductor]})
conductor_show = conductor_df.copy(); conductor_show["Valor"] = conductor_show["Valor"].map(cop)
st.dataframe(conductor_show, use_container_width=True, hide_index=True)

st.divider(); st.markdown("<div class='section-title'>📌 Recargos discriminados</div>", unsafe_allow_html=True)
recargos_df = pd.DataFrame({"Concepto": ["Ordinarias diurnas", "Ordinarias nocturnas base", "Recargo nocturno", "Extras diurnas", "Extras nocturnas", "Dominicales", "Festivos"], "Horas": [h_ord_dia, h_ord_noc, h_noc, h_ext_dia, h_ext_noc, h_dom, h_fes], "% aplicado": ["100%", "100%", pct(rec_nocturno), f"100% + {pct(rec_extra_diurna)}", f"100% + {pct(rec_extra_nocturna)}", pct(rec_dominical), pct(rec_festivo)], "Valor hora/base": [vh, vh, vh, vh, vh, vh, vh], "Valor total": [valor_ord_dia, valor_ord_noc_base, valor_rec_noc, valor_ext_dia, valor_ext_noc, valor_dom, valor_fes]})
recargos_show = recargos_df.copy(); recargos_show["Horas"] = recargos_show["Horas"].map(hrs); recargos_show["Valor hora/base"] = recargos_show["Valor hora/base"].map(cop); recargos_show["Valor total"] = recargos_show["Valor total"].map(cop)
st.dataframe(recargos_show, use_container_width=True, hide_index=True)
st.bar_chart(recargos_df.set_index("Concepto")[["Valor total"]])

st.divider(); st.markdown("<div class='section-title'>🏢 Costo empresa: prestaciones, aportes, parafiscales y vehículo</div>", unsafe_allow_html=True)
empresa_rows = [("PRESTACIONES", "Prima", prima_pct, base_salarial, prima), ("PRESTACIONES", "Cesantías", cesantias_pct, base_salarial, cesantias), ("PRESTACIONES", "Intereses cesantías", interes_ces_pct, base_salarial, interes_ces), ("PRESTACIONES", "Vacaciones", vacaciones_pct, base_salarial, vacaciones), ("APORTES", "Pensión empresa", pension_emp_pct, base_salarial, pension_emp), ("APORTES", "CCP / Caja", ccp_pct, base_salarial, ccp), ("APORTES", "ARL", arl_pct, base_salarial, arl), ("SALUD/PARAFISCALES", "Salud empresa", salud_emp_pct, base_salarial, salud_emp), ("SALUD/PARAFISCALES", "SENA", sena_pct, base_salarial, sena), ("SALUD/PARAFISCALES", "ICBF", icbf_pct, base_salarial, icbf), ("SALUD/PARAFISCALES", "FSP", fsp_pct, base_salarial, fsp), ("VEHÍCULO", "Dotación", 0, 0, dotacion), ("VEHÍCULO", "Alimentación", 0, 0, alimentacion), ("VEHÍCULO", "Lavado general vehículo", 0, 0, lavado), ("VEHÍCULO", "Estadía", 0, 0, estadia), ("VEHÍCULO", "Peaje con chip", 0, 0, peaje), ("VEHÍCULO", "Combustible", 0, 0, combustible), ("VEHÍCULO", "Parqueadero", 0, 0, parqueadero), ("VEHÍCULO", "Mantenimiento", 0, 0, mantenimiento)]
empresa_df = pd.DataFrame(empresa_rows, columns=["Bloque", "Concepto", "% aplicado", "Base cálculo", "Valor"])
empresa_show = empresa_df.copy(); empresa_show["% aplicado"] = empresa_show["% aplicado"].map(lambda x: "" if x == 0 else pct(x)); empresa_show["Base cálculo"] = empresa_show["Base cálculo"].map(lambda x: "" if x == 0 else cop(x)); empresa_show["Valor"] = empresa_show["Valor"].map(cop)
st.dataframe(empresa_show, use_container_width=True, hide_index=True)
st.bar_chart(empresa_df.groupby("Bloque")[["Valor"]].sum())

st.divider(); st.markdown("<div class='section-title'>📅 Programación visual 14x7</div>", unsafe_allow_html=True)
html = "<table style='width:100%; border-collapse:separate; border-spacing:7px;'>"
for semana in sorted(programacion["Semana"].unique()):
    html += "<tr>"
    for _, r in programacion[programacion["Semana"] == semana].iterrows():
        celda = f"<div style='font-weight:800;font-size:16px;color:#111827'>{int(r['Día'])}</div><div style='font-size:12px'>{r['Día semana']}</div><div style='font-size:12px;font-weight:700'>{r['Etiqueta']}</div><div style='font-size:11px'>D {round(r['Horas diurnas'])}h / N {round(r['Horas nocturnas'])}h</div><div style='font-size:11px'>ExD {round(r['Extras diurnas'])}h / ExN {round(r['Extras nocturnas'])}h</div>"
        html += f"<td style='background:{r['Color']}; padding:10px; border-radius:12px; text-align:center; border:1px solid #D1D5DB;'>{celda}</td>"
    html += "</tr>"
html += "</table>"
st.markdown(html, unsafe_allow_html=True)
st.caption("Verde: laborado | Gris: descanso | Morado: nocturnidad | Rojo: dominical | Azul: festivo")

st.divider(); st.markdown("<div class='section-title'>📋 Resumen semanal</div>", unsafe_allow_html=True)
weekly = []
for semana, gp in programacion.groupby("Semana"):
    weekly.append({"Semana": f"Semana {semana}", "Días laborados": int((gp["Estado"] == "LABORA").sum()), "Domingos": int(((gp["Estado"] == "LABORA") & (gp["Es domingo"])).sum()), "Festivos": int(((gp["Estado"] == "LABORA") & (gp["Es festivo"])).sum()), "Horas totales": round(gp["Horas totales"].sum()), "Diurnas": round(gp["Horas diurnas"].sum()), "Nocturnas": round(gp["Horas nocturnas"].sum()), "Extras diurnas": round(gp["Extras diurnas"].sum()), "Extras nocturnas": round(gp["Extras nocturnas"].sum())})
st.dataframe(pd.DataFrame(weekly), use_container_width=True, hide_index=True)

st.divider(); st.markdown("<div class='section-title'>📄 Detalle diario descargable</div>", unsafe_allow_html=True)
detalle = programacion.copy()
for col in ["Horas totales", "Horas diurnas", "Horas nocturnas", "Ordinarias diurnas", "Ordinarias nocturnas", "Extras diurnas", "Extras nocturnas"]:
    detalle[col] = detalle[col].round(2)
st.dataframe(detalle, use_container_width=True, hide_index=True)
st.download_button("⬇️ Descargar detalle diario CSV", data=detalle.to_csv(index=False).encode("utf-8-sig"), file_name=f"detalle_14x7_{mes_nombre}_{anio}.csv", mime="text/csv")
st.success("✅ Dashboard calculado con lógica real de horario, calendario 14x7, domingos, festivos, extras y recargos.")
