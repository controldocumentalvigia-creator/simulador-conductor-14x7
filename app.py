
import calendar
from datetime import date
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Simulador costo conductor 14x7", page_icon="🚐", layout="wide")

st.markdown("""
<style>
.metric-card {
    background: white;
    padding: 18px;
    border-radius: 16px;
    border: 1px solid #e6e9ef;
}
</style>
""", unsafe_allow_html=True)

st.title("🚐 Simulador de costo conductor 14x7")
st.caption("Proyección gerencial simple: salario, extras, nocturnas, dominicales/festivos y bolsa mensual estimada.")

MONTHS = {
    "Enero": 1, "Febrero": 2, "Marzo": 3, "Abril": 4, "Mayo": 5, "Junio": 6,
    "Julio": 7, "Agosto": 8, "Septiembre": 9, "Octubre": 10, "Noviembre": 11, "Diciembre": 12
}

def cop(value):
    return f"${value:,.0f}".replace(",", ".")

def dominical_rate(year):
    if year >= 2027:
        return 1.00
    if year == 2026:
        return 0.90
    return 0.80

def build_calendar(year, month, start_day, hours_day, ordinary_day, pct_night):
    days_in_month = calendar.monthrange(year, month)[1]
    records = []
    cycle_day = start_day

    for d in range(1, days_in_month + 1):
        current = date(year, month, d)
        day_cycle = ((cycle_day - 1) % 21) + 1
        is_work = day_cycle <= 14
        is_sunday = current.weekday() == 6

        worked_hours = hours_day if is_work else 0
        ordinary_hours = min(ordinary_day, worked_hours)
        extra_hours = max(0, worked_hours - ordinary_hours)
        night_hours = worked_hours * pct_night
        extra_night_hours = extra_hours * pct_night
        extra_day_hours = extra_hours - extra_night_hours

        records.append({
            "Fecha": current,
            "Día": d,
            "Semana_mes": ((d - 1) // 7) + 1,
            "Día_semana": ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"][current.weekday()],
            "Día_ciclo_14x7": day_cycle,
            "Estado": "LABORA" if is_work else "DESCANSO",
            "Es_domingo": is_sunday,
            "Horas": worked_hours,
            "Horas_ordinarias_día": ordinary_hours,
            "Horas_extra_base_día": extra_hours,
            "Horas_nocturnas": night_hours,
            "Horas_extra_diurnas": extra_day_hours,
            "Horas_extra_nocturnas": extra_night_hours,
            "Etiqueta": "DOMINICAL" if is_work and is_sunday else ("LABORA" if is_work else "DESCANSO")
        })
        cycle_day += 1

    return pd.DataFrame(records)

with st.sidebar:
    st.header("⚙️ Parámetros")
    year = st.number_input("Año", min_value=2025, max_value=2035, value=2026, step=1)
    month_name = st.selectbox("Mes", list(MONTHS.keys()), index=4)
    month = MONTHS[month_name]
    drivers = st.number_input("Cantidad de conductores", min_value=1, max_value=500, value=1, step=1)
    city = st.selectbox("Ciudad", ["Bogotá", "Medellín", "Cali", "Barranquilla", "Ibagué", "Otra"])
    operation = st.selectbox("Tipo de operación", ["Transporte especial", "Empresarial", "Escolar", "Nocturna", "Mixta", "Otra"])
    start_day = st.slider("Día del ciclo 14x7 al iniciar el mes", 1, 21, 1)

    st.divider()
    st.subheader("💰 Base salarial")
    salary = st.number_input("SMLV / salario base mensual", min_value=0, value=1750905, step=10000)
    transport_allowance = st.number_input("Auxilio transporte", min_value=0, value=249095, step=1000)
    monthly_bonus = st.number_input("Bonificación mensual estimada por conductor", min_value=0, value=0, step=50000)
    provision_pct = st.slider("Carga prestacional/seguridad social estimada %", 0, 70, 45, 1) / 100

    st.divider()
    st.subheader("⏱️ Jornada")
    weekly_limit = st.number_input("Jornada máxima semanal", min_value=1, value=44, step=1)
    hours_day = st.number_input("Horas disponibles por día laborado", min_value=1.0, max_value=24.0, value=12.0, step=0.5)
    ordinary_day = st.number_input("Horas ordinarias base día", min_value=1.0, max_value=12.0, value=8.0, step=0.5)
    pct_night = st.slider("% de horas nocturnas dentro del turno", 0, 100, 30, 5) / 100

    st.divider()
    st.subheader("📌 Recargos")
    night_rate = st.number_input("Recargo nocturno %", min_value=0, value=35, step=1) / 100
    extra_day_rate = st.number_input("Extra diurna %", min_value=0, value=25, step=1) / 100
    extra_night_rate = st.number_input("Extra nocturna %", min_value=0, value=75, step=1) / 100
    sunday_rate = st.number_input("Dominical/festivo %", min_value=0, value=int(dominical_rate(year)*100), step=1) / 100

df = build_calendar(year, month, start_day, hours_day, ordinary_day, pct_night)

hour_value = salary / 220 if salary else 0
total_hours = df["Horas"].sum()
work_days = int((df["Estado"] == "LABORA").sum())
rest_days = int((df["Estado"] == "DESCANSO").sum())
sundays_worked = int(((df["Estado"] == "LABORA") & (df["Es_domingo"])).sum())
night_hours = df["Horas_nocturnas"].sum()
extra_day_hours = df["Horas_extra_diurnas"].sum()
extra_night_hours = df["Horas_extra_nocturnas"].sum()
sunday_hours = df.loc[(df["Estado"] == "LABORA") & (df["Es_domingo"]), "Horas"].sum()

base_month = salary + transport_allowance
night_cost = night_hours * hour_value * night_rate
extra_day_cost = extra_day_hours * hour_value * (1 + extra_day_rate)
extra_night_cost = extra_night_hours * hour_value * (1 + extra_night_rate)
sunday_cost = sunday_hours * hour_value * sunday_rate
variable_cost = night_cost + extra_day_cost + extra_night_cost + sunday_cost + monthly_bonus
provisions = (salary + variable_cost) * provision_pct
monthly_cost_one = base_month + variable_cost + provisions
monthly_cost_total = monthly_cost_one * drivers
annual_cost_total = monthly_cost_total * 12

weekly_cost = []
for week, group in df.groupby("Semana_mes"):
    wh = group["Horas"].sum()
    proportion = wh / total_hours if total_hours else 0
    weekly_cost.append({
        "Semana": f"Semana {week}",
        "Horas": wh,
        "Días laborados": int((group["Estado"] == "LABORA").sum()),
        "Días descanso": int((group["Estado"] == "DESCANSO").sum()),
        "Costo estimado": monthly_cost_one * proportion
    })
weekly_cost_df = pd.DataFrame(weekly_cost)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Costo mensual total", cop(monthly_cost_total))
c2.metric("Costo mensual por conductor", cop(monthly_cost_one))
c3.metric("Costo anual proyectado", cop(annual_cost_total))
c4.metric("Horas mes por conductor", f"{total_hours:,.1f}".replace(",", "."))

c5, c6, c7, c8 = st.columns(4)
c5.metric("Días laborados", work_days)
c6.metric("Días descanso", rest_days)
c7.metric("Dominicales trabajados", sundays_worked)
c8.metric("Horas nocturnas estimadas", f"{night_hours:,.1f}".replace(",", "."))

st.divider()

left, right = st.columns([1.2, 1])

with left:
    st.subheader(f"📅 Calendario operacional - {month_name} {year}")
    html = "<table style='width:100%; border-collapse:separate; border-spacing:6px;'>"
    for week in sorted(df["Semana_mes"].unique()):
        html += "<tr>"
        week_data = df[df["Semana_mes"] == week]
        for _, r in week_data.iterrows():
            if r["Estado"] == "DESCANSO":
                bg = "#D9D9D9"
            elif r["Es_domingo"]:
                bg = "#F4CCCC"
            elif r["Horas_nocturnas"] > 0:
                bg = "#D9D2E9"
            else:
                bg = "#D9EAD3"
            cell = f"{int(r['Día'])}<br>{r['Día_semana']}<br>{r['Etiqueta']}<br>{r['Horas']} h"
            html += f"<td style='background:{bg}; padding:10px; border-radius:10px; text-align:center; font-size:13px;'>{cell}</td>"
        html += "</tr>"
    html += "</table>"
    st.markdown(html, unsafe_allow_html=True)
    st.caption("Verde: labora | Gris: descanso | Morado: contiene nocturno | Rojo: dominical laborado")

with right:
    st.subheader("💸 Costo por semana")
    fig = px.bar(weekly_cost_df, x="Semana", y="Costo estimado", text="Costo estimado")
    fig.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
    fig.update_layout(yaxis_title="COP", xaxis_title="", height=420)
    st.plotly_chart(fig, use_container_width=True)

st.divider()

a, b = st.columns(2)

with a:
    st.subheader("📊 Composición del costo variable")
    comp = pd.DataFrame({
        "Concepto": ["Recargo nocturno", "Extras diurnas", "Extras nocturnas", "Dominicales", "Bonos"],
        "Valor": [night_cost, extra_day_cost, extra_night_cost, sunday_cost, monthly_bonus]
    })
    fig2 = px.pie(comp, names="Concepto", values="Valor", hole=0.45)
    st.plotly_chart(fig2, use_container_width=True)

with b:
    st.subheader("📋 Resumen semanal")
    show_week = weekly_cost_df.copy()
    show_week["Costo estimado"] = show_week["Costo estimado"].map(cop)
    st.dataframe(show_week, use_container_width=True, hide_index=True)

st.subheader("📄 Detalle diario")
detail = df[[
    "Fecha", "Semana_mes", "Día_semana", "Día_ciclo_14x7", "Estado", "Es_domingo",
    "Horas", "Horas_ordinarias_día", "Horas_extra_diurnas", "Horas_extra_nocturnas", "Horas_nocturnas"
]].copy()
st.dataframe(detail, use_container_width=True, hide_index=True)

csv = detail.to_csv(index=False).encode("utf-8-sig")
st.download_button("⬇️ Descargar detalle CSV", data=csv, file_name="detalle_simulador_14x7.csv", mime="text/csv")

st.info("Este simulador es una proyección gerencial. Para liquidación oficial de nómina, debe validarse con el área laboral/contable y la normatividad vigente.")
