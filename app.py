import calendar
from datetime import date, datetime, time, timedelta
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Simulador conductor + vehículo 14x7", page_icon="🚐", layout="wide")

AZUL = "#123A5A"
AZUL2 = "#1E5A84"
FONDO = "#F6F9FC"

st.markdown(f"""
<style>
.stApp {{ background: {FONDO}; }}
.block-container {{ padding-top: 1.2rem; }}
[data-testid="stSidebar"] {{ background: #ffffff; border-right: 1px solid #d8e1ea; }}
h1, h2, h3 {{ color: {AZUL}; }}
.kpi-title {{font-size:13px;color:#5b6770;margin-bottom:4px;}}
.kpi-value {{font-size:24px;font-weight:800;color:{AZUL};}}
.kpi-card {{background:white;border:1px solid #d8e1ea;border-radius:16px;padding:16px;box-shadow:0 2px 8px rgba(18,58,90,.08);}}
.section-card {{background:white;border:1px solid #d8e1ea;border-radius:16px;padding:18px;margin-top:12px;}}
.header-box {{background:linear-gradient(90deg,{AZUL},{AZUL2});color:white;padding:22px;border-radius:18px;margin-bottom:18px;}}
.header-box h1 {{color:white;margin:0;font-size:30px;}}
.header-box p {{color:#eaf3fb;margin:6px 0 0 0;}}
</style>
""", unsafe_allow_html=True)

st.markdown("""
<div class='header-box'>
<h1>🚐 Simulador financiero-operacional 14x7</h1>
<p>Transporte especial empresarial · Costo conductor + vehículo · Neto a pagar al conductor</p>
</div>
""", unsafe_allow_html=True)

MESES = {"Enero":1,"Febrero":2,"Marzo":3,"Abril":4,"Mayo":5,"Junio":6,"Julio":7,"Agosto":8,"Septiembre":9,"Octubre":10,"Noviembre":11,"Diciembre":12}


def cop(v):
    return f"${round(float(v)):,}".replace(",", ".")


def hrs(v):
    return f"{round(float(v)):,} h".replace(",", ".")


def pct(v):
    return f"{v*100:.2f}%"


def tarifa_dom(anio):
    return 1.00 if anio >= 2027 else (0.90 if anio == 2026 else 0.80)


def rango_horas(inicio, fin):
    base = datetime(2026, 1, 1)
    ini = datetime.combine(base, inicio)
    fi = datetime.combine(base, fin)
    if fi <= ini:
        fi += timedelta(days=1)
    return (fi - ini).total_seconds() / 3600, ini, fi


def partir_diurna_nocturna(inicio, fin):
    total, ini, fi = rango_horas(inicio, fin)
    cur = ini
    paso = timedelta(minutes=15)
    h_dia = 0.0
    h_noc = 0.0
    while cur < fi:
        sig = min(cur + paso, fi)
        bloque = (sig - cur).total_seconds() / 3600
        t = cur.time()
        if t >= time(19, 0) or t < time(6, 0):
            h_noc += bloque
        else:
            h_dia += bloque
        cur = sig
    return round(h_dia, 2), round(h_noc, 2), round(total, 2)


def crear_programacion(anio, mes, ciclo_ini, hora_ini, hora_fin, horas_ordinarias, festivos_manual):
    dias = calendar.monthrange(anio, mes)[1]
    h_dia_turno, h_noc_turno, h_total_turno = partir_diurna_nocturna(hora_ini, hora_fin)
    filas = []
    ciclo = ciclo_ini
    festivos_asignados = 0
    for d in range(1, dias + 1):
        f = date(anio, mes, d)
        dia_ciclo = ((ciclo - 1) % 21) + 1
        labora = dia_ciclo <= 14
        domingo = f.weekday() == 6
        festivo = False
        if labora and (not domingo) and festivos_asignados < festivos_manual:
            festivo = True
            festivos_asignados += 1

        h_total = h_total_turno if labora else 0
        h_dia = h_dia_turno if labora else 0
        h_noc = h_noc_turno if labora else 0
        h_extra = max(0, h_total - horas_ordinarias)
        p_dia = h_dia / h_total if h_total else 0
        p_noc = h_noc / h_total if h_total else 0
        h_extra_dia = h_extra * p_dia
        h_extra_noc = h_extra * p_noc
        h_ord_dia = max(0, h_dia - h_extra_dia)
        h_ord_noc = max(0, h_noc - h_extra_noc)

        if not labora:
            estado, color = "DESCANSO", "#E5E7EB"
        elif festivo:
            estado, color = "FESTIVO", "#CFE8FF"
        elif domingo:
            estado, color = "DOMINICAL", "#FFD6D6"
        elif h_noc > 0:
            estado, color = "NOCTURNO", "#E4D7F5"
        else:
            estado, color = "LABORA", "#DDF2DF"

        filas.append({
            "Fecha": f, "Día": d, "Semana": ((d - 1) // 7) + 1,
            "Día semana": ["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"][f.weekday()],
            "Día ciclo 14x7": dia_ciclo, "Estado": estado, "Color": color,
            "Dominical": domingo and labora, "Festivo": festivo,
            "Horas totales": h_total, "Horas diurnas": h_dia, "Horas nocturnas": h_noc,
            "Ordinarias diurnas": h_ord_dia, "Ordinarias nocturnas": h_ord_noc,
            "Extras diurnas": h_extra_dia, "Extras nocturnas": h_extra_noc
        })
        ciclo += 1
    return pd.DataFrame(filas)

with st.sidebar:
    st.header("⚙️ Parámetros del simulador")
    anio = st.number_input("Año", 2025, 2035, 2026)
    mes_nombre = st.selectbox("Mes", list(MESES.keys()), index=4)
    mes = MESES[mes_nombre]
    conductores = st.number_input("Cantidad de conductores", 1, 500, 1)
    dia_ciclo = st.slider("Día del ciclo 14x7 al iniciar el mes", 1, 21, 1)

    st.subheader("🕐 Programación")
    hora_ini = st.time_input("Hora inicio", value=time(3, 0), step=1800)
    hora_fin = st.time_input("Hora finalización", value=time(15, 0), step=1800)
    horas_disponibles = st.number_input("Horas disponibles por día", 1.0, 15.0, 12.0, step=0.5)
    horas_ordinarias = st.number_input("Horas ordinarias base día", 1.0, 12.0, 8.0, step=0.5)
    limite_fatiga = st.number_input("Límite de fatiga", 1.0, 24.0, 15.0, step=0.5)

    st.subheader("💰 Base conductor")
    smlv = st.number_input("SMLV", 0, value=1750905, step=10000)
    bono_disp = st.number_input("Bono disponibilidad", 0, value=214000, step=10000)
    bono_res = st.number_input("Bono resultados", 0, value=240492, step=10000)
    bono_com = st.number_input("Bono comunicación", 0, value=30000, step=5000)
    transporte = st.number_input("Valor transporte", 0, value=0, step=10000)

    st.subheader("🎯 Comisión por productividad")
    produccion = st.number_input("Producción del vehículo", 0, value=16000000, step=100000)
    meta = st.number_input("Meta mínima", 0, value=16000000, step=100000)
    pct_comision = st.slider("% comisión", 0.0, 10.0, 2.0, 0.5) / 100

    st.subheader("📌 Recargos")
    rec_noc = st.number_input("Recargo nocturno %", 0.0, 200.0, 35.0, step=1.0) / 100
    rec_ext_dia = st.number_input("Extra diurna %", 0.0, 200.0, 25.0, step=1.0) / 100
    rec_ext_noc = st.number_input("Extra nocturna %", 0.0, 200.0, 75.0, step=1.0) / 100
    rec_dom = st.number_input("Dominical %", 0.0, 200.0, tarifa_dom(anio)*100, step=1.0) / 100
    rec_fes = st.number_input("Festivo %", 0.0, 200.0, tarifa_dom(anio)*100, step=1.0) / 100
    festivos_mes = st.number_input("Festivos laborados", 0, 10, 0)

    st.subheader("🧾 Prestaciones y aportes")
    prima_p = st.number_input("Prima %", 0.0, 20.0, 8.33, step=0.01) / 100
    ces_p = st.number_input("Cesantías %", 0.0, 20.0, 8.33, step=0.01) / 100
    int_ces_p = st.number_input("Intereses cesantías %", 0.0, 10.0, 1.00, step=0.01) / 100
    vac_p = st.number_input("Vacaciones %", 0.0, 20.0, 4.17, step=0.01) / 100
    pen_emp_p = st.number_input("Pensión empresa %", 0.0, 30.0, 12.00, step=0.01) / 100
    ccp_p = st.number_input("CCP / Caja %", 0.0, 20.0, 4.00, step=0.01) / 100
    arl_p = st.number_input("ARL %", 0.0, 20.0, 6.96, step=0.01) / 100
    salud_emp_p = st.number_input("Salud empresa %", 0.0, 20.0, 8.50, step=0.01) / 100
    sena_p = st.number_input("SENA %", 0.0, 10.0, 0.00, step=0.01) / 100
    icbf_p = st.number_input("ICBF %", 0.0, 10.0, 0.00, step=0.01) / 100
    fsp_p = st.number_input("FSP %", 0.0, 10.0, 0.00, step=0.01) / 100

    st.subheader("💵 Descuentos conductor")
    salud_trab_p = st.number_input("Salud empleado %", 0.0, 20.0, 4.00, step=0.01) / 100
    pension_trab_p = st.number_input("Pensión empleado %", 0.0, 20.0, 4.00, step=0.01) / 100
    otros_desc = st.number_input("Otros descuentos", 0, value=0, step=10000)

    st.subheader("🚐 Costos_ADIC_vehículo+Conductor")
    dotacion = st.number_input("Dotación", 0, value=0, step=10000)
    alimentacion = st.number_input("Alimentación", 0, value=0, step=10000)
    lavado = st.number_input("Lavado general", 0, value=0, step=10000)
    estadia = st.number_input("Estadía", 0, value=0, step=10000)
    peaje = st.number_input("Peaje con chip", 0, value=0, step=10000)
    combustible = st.number_input("Combustible", 0, value=0, step=10000)
    parqueadero = st.number_input("Parqueadero", 0, value=0, step=10000)
    mantenimiento = st.number_input("Mantenimiento", 0, value=0, step=10000)

prog = crear_programacion(anio, mes, dia_ciclo, hora_ini, hora_fin, horas_ordinarias, int(festivos_mes))
h_total_dia, _, _ = rango_horas(hora_ini, hora_fin)

base_salarial = smlv + bono_res + bono_disp
valor_hora = base_salarial / 220 if base_salarial else 0

h_dia = prog["Horas diurnas"].sum(); h_noc = prog["Horas nocturnas"].sum()
h_ord_dia = prog["Ordinarias diurnas"].sum(); h_ord_noc = prog["Ordinarias nocturnas"].sum()
h_ext_dia = prog["Extras diurnas"].sum(); h_ext_noc = prog["Extras nocturnas"].sum()
h_dom = prog.loc[prog["Dominical"], "Horas totales"].sum(); h_fes = prog.loc[prog["Festivo"], "Horas totales"].sum()
dom_count = int(prog["Dominical"].sum()); fes_count = int(prog["Festivo"].sum())

comision = produccion * pct_comision if produccion >= meta else 0

c_rec_noc = h_noc * valor_hora * rec_noc
c_ext_dia = h_ext_dia * valor_hora * (1 + rec_ext_dia)
c_ext_noc = h_ext_noc * valor_hora * (1 + rec_ext_noc)
c_dom = h_dom * valor_hora * rec_dom
c_fes = h_fes * valor_hora * rec_fes
c_recargos = c_rec_noc + c_ext_dia + c_ext_noc + c_dom + c_fes

prestaciones = {
    "Prima": base_salarial * prima_p,
    "Cesantías": base_salarial * ces_p,
    "Intereses cesantías": base_salarial * int_ces_p,
    "Vacaciones": base_salarial * vac_p
}
aportes = {
    "Pensión empresa": base_salarial * pen_emp_p,
    "CCP / Caja": base_salarial * ccp_p,
    "ARL": base_salarial * arl_p,
    "Salud empresa": base_salarial * salud_emp_p,
    "SENA": base_salarial * sena_p,
    "ICBF": base_salarial * icbf_p,
    "FSP": base_salarial * fsp_p
}
vehiculo = {
    "Dotación": dotacion, "Alimentación": alimentacion, "Lavado general": lavado,
    "Estadía": estadia, "Peaje con chip": peaje, "Combustible": combustible,
    "Parqueadero": parqueadero, "Mantenimiento": mantenimiento
}

total_prest = sum(prestaciones.values())
total_aportes = sum(aportes.values())
total_vehiculo = sum(vehiculo.values())

devengado = smlv + bono_disp + bono_res + bono_com + transporte + comision + c_recargos
desc_salud = base_salarial * salud_trab_p
desc_pension = base_salarial * pension_trab_p
total_desc = desc_salud + desc_pension + otros_desc
neto = devengado - total_desc

costo_conductor = devengado + total_prest + total_aportes
costo_conductor_vehiculo = costo_conductor + total_vehiculo
costo_flota = costo_conductor_vehiculo * conductores
costo_anual = costo_flota * 12
ratio = costo_conductor_vehiculo / neto if neto else 0

# KPIs
st.subheader("📌 Centro de control ejecutivo")
cols = st.columns(4)
items = [
    ("Costo conductor", costo_conductor), ("Costo vehículo", total_vehiculo),
    ("Conductor + vehículo", costo_conductor_vehiculo), ("Neto conductor", neto),
]
for col, (lab, val) in zip(cols, items):
    col.markdown(f"<div class='kpi-card'><div class='kpi-title'>{lab}</div><div class='kpi-value'>{cop(val)}</div></div>", unsafe_allow_html=True)
cols2 = st.columns(4)
items2 = [("Costo mensual flota", costo_flota), ("Costo anual", costo_anual), ("Base salarial", base_salarial), ("Empresa paga por cada $1 neto", ratio)]
for col, (lab, val) in zip(cols2, items2):
    shown = f"${val:.2f}" if "cada" in lab else cop(val)
    col.markdown(f"<div class='kpi-card'><div class='kpi-title'>{lab}</div><div class='kpi-value'>{shown}</div></div>", unsafe_allow_html=True)

st.subheader("⏱️ Horas y alertas")
c1,c2,c3,c4,c5,c6 = st.columns(6)
c1.metric("Diurnas", hrs(h_dia)); c2.metric("Nocturnas", hrs(h_noc)); c3.metric("Extras", hrs(h_ext_dia+h_ext_noc)); c4.metric("Dominicales", dom_count); c5.metric("Festivos", fes_count); c6.metric("Horas/día", hrs(h_total_dia))
if h_total_dia > limite_fatiga:
    st.error(f"🚨 Alerta de fatiga: {hrs(h_total_dia)} supera el límite {hrs(limite_fatiga)}.")
elif horas_disponibles > 12:
    st.warning("⚠️ Horas disponibles superiores a 12. Validar si el excedente se paga como adicional/disponibilidad.")
else:
    st.success("✅ Jornada dentro de parámetros operativos configurados.")

# Desgloses
st.subheader("💳 Lo que llega al conductor")
conductor_df = pd.DataFrame([
    ["Salario base", "", "", smlv], ["Bono disponibilidad", "", "", bono_disp], ["Bono resultados", "", "", bono_res],
    ["Bono comunicación", "", "", bono_com], ["Transporte", "", "", transporte], ["Comisión productividad", f"{pct(pct_comision)}", f"Meta {cop(meta)}", comision],
    ["Recargos/extras/dominicales", "", "Ver tabla de recargos", c_recargos], ["Salud empleado", pct(salud_trab_p), cop(base_salarial), -desc_salud],
    ["Pensión empleado", pct(pension_trab_p), cop(base_salarial), -desc_pension], ["Otros descuentos", "", "", -otros_desc], ["NETO A PAGAR", "", "", neto]
], columns=["Concepto", "% aplicado", "Base / soporte", "Valor"])
show = conductor_df.copy(); show["Valor"] = show["Valor"].map(cop)
st.dataframe(show, use_container_width=True, hide_index=True)

st.subheader("🏢 Costo empresa detallado")
rows = [["Devengado conductor", "", "", devengado]]
for k,v in prestaciones.items(): rows.append([k, pct({"Prima":prima_p,"Cesantías":ces_p,"Intereses cesantías":int_ces_p,"Vacaciones":vac_p}[k]), cop(base_salarial), v])
for k,v in aportes.items():
    pmap = {"Pensión empresa":pen_emp_p,"CCP / Caja":ccp_p,"ARL":arl_p,"Salud empresa":salud_emp_p,"SENA":sena_p,"ICBF":icbf_p,"FSP":fsp_p}
    rows.append([k, pct(pmap[k]), cop(base_salarial), v])
for k,v in vehiculo.items(): rows.append([k, "", "Costo operativo", v])
rows.append(["COSTO TOTAL CONDUCTOR + VEHÍCULO", "", "", costo_conductor_vehiculo])
empresa_df = pd.DataFrame(rows, columns=["Concepto", "% aplicado", "Base / soporte", "Valor"])
show = empresa_df.copy(); show["Valor"] = show["Valor"].map(cop)
st.dataframe(show, use_container_width=True, hide_index=True)

st.subheader("📌 Recargos discriminados")
rec_df = pd.DataFrame([
    ["Recargo nocturno", hrs(h_noc), pct(rec_noc), cop(valor_hora), c_rec_noc],
    ["Extras diurnas", hrs(h_ext_dia), pct(rec_ext_dia), cop(valor_hora), c_ext_dia],
    ["Extras nocturnas", hrs(h_ext_noc), pct(rec_ext_noc), cop(valor_hora), c_ext_noc],
    ["Dominicales", hrs(h_dom), pct(rec_dom), cop(valor_hora), c_dom],
    ["Festivos", hrs(h_fes), pct(rec_fes), cop(valor_hora), c_fes],
], columns=["Concepto", "Horas", "% aplicado", "Valor hora base", "Valor"])
show = rec_df.copy(); show["Valor"] = show["Valor"].map(cop)
st.dataframe(show, use_container_width=True, hide_index=True)

st.subheader("📊 Gráficos ejecutivos")
g1, g2 = st.columns(2)
with g1:
    st.write("Composición costo empresa")
    st.bar_chart(pd.DataFrame({"Valor":[devengado,total_prest,total_aportes,total_vehiculo]}, index=["Devengado","Prestaciones","Aportes","Vehículo"]))
with g2:
    st.write("Resumen horas")
    st.bar_chart(pd.DataFrame({"Horas":[round(h_ord_dia),round(h_ord_noc),round(h_ext_dia),round(h_ext_noc),round(h_dom),round(h_fes)]}, index=["Ord. día","Ord. noche","Extra día","Extra noche","Dom","Fest"]))

st.subheader(f"📅 Programación visual 14x7 - {mes_nombre} {anio}")
html = "<table style='width:100%; border-collapse:separate; border-spacing:7px;'>"
for sem in sorted(prog["Semana"].unique()):
    html += "<tr>"
    for _, r in prog[prog["Semana"] == sem].iterrows():
        cell = f"<b>{int(r['Día'])}</b><br>{r['Día semana']}<br>{r['Estado']}<br>D {round(r['Horas diurnas'])}h / N {round(r['Horas nocturnas'])}h"
        html += f"<td style='background:{r['Color']};padding:10px;border-radius:12px;text-align:center;border:1px solid #d8e1ea;font-size:12px;'>{cell}</td>"
    html += "</tr>"
html += "</table>"
st.markdown(html, unsafe_allow_html=True)
st.caption("Verde: labora · Gris: descanso · Morado: nocturno · Rojo: dominical · Azul: festivo")

st.subheader("📋 Resumen semanal")
weekly=[]
for sem, gp in prog.groupby("Semana"):
    wd=gp["Horas diurnas"].sum(); wn=gp["Horas nocturnas"].sum(); wed=gp["Extras diurnas"].sum(); wen=gp["Extras nocturnas"].sum()
    wdom=gp.loc[gp["Dominical"],"Horas totales"].sum(); wfes=gp.loc[gp["Festivo"],"Horas totales"].sum()
    costo=(wn*valor_hora*rec_noc)+(wed*valor_hora*(1+rec_ext_dia))+(wen*valor_hora*(1+rec_ext_noc))+(wdom*valor_hora*rec_dom)+(wfes*valor_hora*rec_fes)
    weekly.append([f"Semana {sem}", round(gp["Horas totales"].sum()), round(wd), round(wn), round(wed), round(wen), round(wdom), round(wfes), cop(costo)])
st.dataframe(pd.DataFrame(weekly, columns=["Semana","Horas totales","Diurnas","Nocturnas","Extras diurnas","Extras nocturnas","Dominicales","Festivas","Costo aprox."]), use_container_width=True, hide_index=True)

st.subheader("📄 Detalle diario descargable")
det = prog.copy()
for col in ["Horas totales","Horas diurnas","Horas nocturnas","Ordinarias diurnas","Ordinarias nocturnas","Extras diurnas","Extras nocturnas"]:
    det[col] = det[col].round(0).astype(int)
st.dataframe(det.drop(columns=["Color"]), use_container_width=True, hide_index=True)
st.download_button("⬇️ Descargar CSV", data=det.drop(columns=["Color"]).to_csv(index=False).encode("utf-8-sig"), file_name=f"simulador_14x7_{mes_nombre}_{anio}.csv", mime="text/csv")
st.info("Simulador gerencial. Validar liquidación oficial con área contable/laboral según naturaleza salarial de bonos, ARL real y normas vigentes.")
