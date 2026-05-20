
import calendar
from datetime import date, datetime, time, timedelta
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="Simulador costo conductor 14x7", page_icon="🚐", layout="wide")
st.title("🚐 Simulador gerencial costo conductor 14x7")
st.caption("Costo mensual detallado: salario, bonos, transporte, diurnas, nocturnas, dominicales, festivos, recargos y aportes empresa.")

MONTHS = {
    "Enero": 1, "Febrero": 2, "Marzo": 3, "Abril": 4, "Mayo": 5, "Junio": 6,
    "Julio": 7, "Agosto": 8, "Septiembre": 9, "Octubre": 10, "Noviembre": 11, "Diciembre": 12
}

def cop(value):
    return f"${value:,.0f}".replace(",", ".")

def default_dominical_rate(year):
    if year >= 2027:
        return 100
    if year == 2026:
        return 90
    return 80

def hours_between(start_t, end_t):
    base_date = datetime(2026, 1, 1)
    start_dt = datetime.combine(base_date, start_t)
    end_dt = datetime.combine(base_date, end_t)
    if end_dt <= start_dt:
        end_dt += timedelta(days=1)
    return (end_dt - start_dt).total_seconds() / 3600, start_dt, end_dt

def night_hours_between(start_t, end_t):
    total, start_dt, end_dt = hours_between(start_t, end_t)
    cursor = start_dt
    night = 0.0
    step = timedelta(minutes=15)
    while cursor < end_dt:
        nxt = min(cursor + step, end_dt)
        h = cursor.time()
        if (h >= time(19, 0)) or (h < time(6, 0)):
            night += (nxt - cursor).total_seconds() / 3600
        cursor = nxt
    return round(night, 2)

def build_calendar(year, month, start_cycle_day, start_t, end_t, ordinary_day, holidays_worked_manual):
    days_in_month = calendar.monthrange(year, month)[1]
    hours_day, _, _ = hours_between(start_t, end_t)
    night_day = night_hours_between(start_t, end_t)
    day_hours_day = max(0, hours_day - night_day)

    records = []
    cycle_day = start_cycle_day
    holiday_assigned = 0

    for d in range(1, days_in_month + 1):
        current = date(year, month, d)
        day_cycle = ((cycle_day - 1) % 21) + 1
        works = day_cycle <= 14
        is_sunday = current.weekday() == 6

        is_holiday = False
        if works and (not is_sunday) and holiday_assigned < holidays_worked_manual:
            is_holiday = True
            holiday_assigned += 1

        worked_hours = hours_day if works else 0
        night_hours = night_day if works else 0
        day_hours = day_hours_day if works else 0

        ordinary_hours = min(ordinary_day, worked_hours)
        extra_hours = max(0, worked_hours - ordinary_day)

        pct_night = night_hours / worked_hours if worked_hours else 0
        extra_night = extra_hours * pct_night
        extra_day = extra_hours - extra_night

        ordinary_night = max(0, night_hours - extra_night)
        ordinary_daytime = max(0, day_hours - extra_day)

        if not works:
            label, color_type = "DESCANSO", "DESCANSO"
        elif is_holiday:
            label, color_type = "FESTIVO", "FESTIVO"
        elif is_sunday:
            label, color_type = "DOMINICAL", "DOMINICAL"
        elif night_hours > 0:
            label, color_type = "LABORA / NOCT.", "NOCTURNO"
        else:
            label, color_type = "LABORA", "LABORA"

        records.append({
            "Fecha": current,
            "Dia": d,
            "Semana_mes": ((d - 1) // 7) + 1,
            "Dia_semana": ["Lun", "Mar", "Mie", "Jue", "Vie", "Sab", "Dom"][current.weekday()],
            "Dia_ciclo_14x7": day_cycle,
            "Estado": "LABORA" if works else "DESCANSO",
            "Etiqueta": label,
            "Tipo_color": color_type,
            "Es_domingo": is_sunday,
            "Es_festivo": is_holiday,
            "Horas_totales": worked_hours,
            "Horas_diurnas": day_hours,
            "Horas_nocturnas": night_hours,
            "Horas_ordinarias_diurnas": ordinary_daytime,
            "Horas_ordinarias_nocturnas": ordinary_night,
            "Horas_extra_diurnas": extra_day,
            "Horas_extra_nocturnas": extra_night
        })
        cycle_day += 1

    return pd.DataFrame(records)

with st.sidebar:
    st.header("⚙️ Escenario")
    year = st.number_input("Año", min_value=2025, max_value=2035, value=2026, step=1)
    month_name = st.selectbox("Mes", list(MONTHS.keys()), index=4)
    month = MONTHS[month_name]
    drivers = st.number_input("Cantidad de conductores", min_value=1, max_value=500, value=1, step=1)
    operation = st.text_input("Tipo de operación", value="SERVICIO POR LLAMADO")
    start_cycle_day = st.slider("Día del ciclo 14x7 al iniciar el mes", 1, 21, 1)

    st.divider()
    st.subheader("🕐 Horario programado")
    start_time = st.time_input("Hora inicio", value=time(5, 0), step=1800)
    end_time = st.time_input("Hora finalización", value=time(17, 0), step=1800)
    weekly_limit = st.number_input("Jornada máxima semanal", min_value=1, max_value=60, value=44, step=1)
    ordinary_day = st.number_input("Horas ordinarias base día", min_value=1.0, max_value=12.0, value=8.0, step=0.5)

    st.divider()
    st.subheader("💰 Fijos editables")
    salary = st.number_input("Salario base mensual / SMLV", min_value=0, value=1750905, step=10000)
    bono_disponibilidad = st.number_input("Bono disponibilidad", min_value=0, value=214000, step=10000)
    bono_resultados = st.number_input("Bono resultados", min_value=0, value=240492, step=10000)
    bono_comunicacion = st.number_input("Bono comunicación", min_value=0, value=30000, step=5000)
    valor_transporte = st.number_input("Valor transporte / auxilio interno", min_value=0, value=0, step=10000)

    st.divider()
    st.subheader("🎯 Bono por facturación")
    valor_facturado = st.number_input("Valor facturado apoyado", min_value=0, value=5000000, step=100000)
    porcentaje_bono = st.slider("% bonificación sobre facturación", 0.0, 10.0, 2.0, 0.5) / 100
    bono_facturacion = valor_facturado * porcentaje_bono

    st.divider()
    st.subheader("📌 Recargos editables")
    night_rate = st.number_input("Recargo nocturno %", min_value=0, max_value=200, value=35, step=1) / 100
    extra_day_rate = st.number_input("Extra diurna %", min_value=0, max_value=200, value=25, step=1) / 100
    extra_night_rate = st.number_input("Extra nocturna %", min_value=0, max_value=200, value=75, step=1) / 100
    sunday_rate = st.number_input("Dominical %", min_value=0, max_value=200, value=default_dominical_rate(year), step=1) / 100
    holiday_rate = st.number_input("Festivo %", min_value=0, max_value=200, value=default_dominical_rate(year), step=1) / 100
    holidays_worked = st.number_input("Cantidad festivos laborados en el mes", min_value=0, max_value=10, value=0, step=1)

    st.divider()
    st.subheader("🧾 Aportes empresa / parafiscales")
    base_bonos_salariales = st.toggle("Bonos hacen base prestacional/seguridad social", value=False)
    aplicar_exoneracion = st.toggle("Aplicar exoneración salud/SENA/ICBF si aplica", value=True)
    salud_default = 0.0 if aplicar_exoneracion else 8.5
    sena_default = 0.0 if aplicar_exoneracion else 2.0
    icbf_default = 0.0 if aplicar_exoneracion else 3.0
    salud_emp_rate = st.number_input("Salud empleador %", min_value=0.0, max_value=20.0, value=salud_default, step=0.1) / 100
    pension_emp_rate = st.number_input("Pensión empleador %", min_value=0.0, max_value=30.0, value=12.0, step=0.1) / 100
    arl_rate = st.number_input("ARL %", min_value=0.0, max_value=10.0, value=0.522, step=0.1) / 100
    caja_rate = st.number_input("Caja compensación %", min_value=0.0, max_value=10.0, value=4.0, step=0.1) / 100
    sena_rate = st.number_input("SENA %", min_value=0.0, max_value=10.0, value=sena_default, step=0.1) / 100
    icbf_rate = st.number_input("ICBF %", min_value=0.0, max_value=10.0, value=icbf_default, step=0.1) / 100
    prestaciones_rate = st.number_input("Prestaciones estimadas %", min_value=0.0, max_value=50.0, value=21.83, step=0.1) / 100

df = build_calendar(year, month, start_cycle_day, start_time, end_time, ordinary_day, int(holidays_worked))
hours_day, _, _ = hours_between(start_time, end_time)
hour_value = salary / 220 if salary else 0

total_hours = df["Horas_totales"].sum()
day_hours = df["Horas_diurnas"].sum()
night_hours = df["Horas_nocturnas"].sum()
ordinary_day_hours = df["Horas_ordinarias_diurnas"].sum()
ordinary_night_hours = df["Horas_ordinarias_nocturnas"].sum()
extra_day_hours = df["Horas_extra_diurnas"].sum()
extra_night_hours = df["Horas_extra_nocturnas"].sum()
sunday_hours = df.loc[(df["Estado"] == "LABORA") & (df["Es_domingo"]), "Horas_totales"].sum()
holiday_hours = df.loc[(df["Estado"] == "LABORA") & (df["Es_festivo"]), "Horas_totales"].sum()

work_days = int((df["Estado"] == "LABORA").sum())
rest_days = int((df["Estado"] == "DESCANSO").sum())
sundays_worked = int(((df["Estado"] == "LABORA") & (df["Es_domingo"])).sum())
holidays_assigned = int(((df["Estado"] == "LABORA") & (df["Es_festivo"])).sum())

ordinary_day_cost = ordinary_day_hours * hour_value
ordinary_night_base_cost = ordinary_night_hours * hour_value
night_surcharge_cost = night_hours * hour_value * night_rate
extra_day_cost = extra_day_hours * hour_value * (1 + extra_day_rate)
extra_night_cost = extra_night_hours * hour_value * (1 + extra_night_rate)
sunday_cost = sunday_hours * hour_value * sunday_rate
holiday_cost = holiday_hours * hour_value * holiday_rate
all_surcharges_cost = night_surcharge_cost + extra_day_cost + extra_night_cost + sunday_cost + holiday_cost

fixed_bonuses = bono_disponibilidad + bono_resultados + bono_comunicacion
variable_bonus = bono_facturacion
ibc_base = salary + all_surcharges_cost + (fixed_bonuses + variable_bonus if base_bonos_salariales else 0)

salud_emp = ibc_base * salud_emp_rate
pension_emp = ibc_base * pension_emp_rate
arl_emp = ibc_base * arl_rate
caja_emp = ibc_base * caja_rate
sena_emp = ibc_base * sena_rate
icbf_emp = ibc_base * icbf_rate
prestaciones = ibc_base * prestaciones_rate
total_aportes_empresa = salud_emp + pension_emp + arl_emp + caja_emp + sena_emp + icbf_emp + prestaciones

fixed_month = salary + bono_disponibilidad + bono_resultados + bono_comunicacion + valor_transporte
monthly_cost_one = fixed_month + variable_bonus + all_surcharges_cost + total_aportes_empresa
monthly_cost_total = monthly_cost_one * drivers
annual_cost_total = monthly_cost_total * 12

st.subheader("📌 Resultado principal")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Costo mensual total empresa", cop(monthly_cost_total))
k2.metric("Costo mensual por conductor", cop(monthly_cost_one))
k3.metric("Costo anual proyectado", cop(annual_cost_total))
k4.metric("Horas por día programado", f"{hours_day:.1f} h")

k5, k6, k7, k8 = st.columns(4)
k5.metric("Horas diurnas mes", f"{day_hours:.1f} h")
k6.metric("Horas nocturnas mes", f"{night_hours:.1f} h")
k7.metric("Dominicales laborados", sundays_worked)
k8.metric("Festivos laborados", holidays_assigned)

st.divider()
st.subheader("🧾 ¿A qué corresponde el costo mensual por conductor?")

breakdown = pd.DataFrame({
    "Bloque": [
        "A. COSTO FIJO", "A. COSTO FIJO", "A. COSTO FIJO", "A. COSTO FIJO", "A. COSTO FIJO",
        "B. BONO VARIABLE",
        "C. HORAS Y RECARGOS", "C. HORAS Y RECARGOS", "C. HORAS Y RECARGOS", "C. HORAS Y RECARGOS", "C. HORAS Y RECARGOS", "C. HORAS Y RECARGOS",
        "D. APORTES / PARAFISCALES", "D. APORTES / PARAFISCALES", "D. APORTES / PARAFISCALES", "D. APORTES / PARAFISCALES", "D. APORTES / PARAFISCALES", "D. APORTES / PARAFISCALES", "D. APORTES / PARAFISCALES",
        "TOTAL"
    ],
    "Concepto": [
        "1 SMLV / salario base", "Bono disponibilidad", "Bono resultados", "Bono comunicación", "Valor transporte",
        "Bono por facturación",
        "Horas diurnas ordinarias", "Horas nocturnas ordinarias base", "Recargo nocturno", "Horas extras diurnas", "Horas extras nocturnas", "Dominicales y festivos",
        "Salud empleador", "Pensión empleador", "ARL", "Caja de compensación", "SENA", "ICBF", "Prestaciones estimadas",
        "TOTAL POR CONDUCTOR"
    ],
    "Horas/Cantidad": [
        "", "", "", "", "",
        f"{porcentaje_bono*100:.1f}% sobre {cop(valor_facturado)}",
        f"{ordinary_day_hours:.1f} h", f"{ordinary_night_hours:.1f} h", f"{night_hours:.1f} h", f"{extra_day_hours:.1f} h", f"{extra_night_hours:.1f} h", f"{sundays_worked} dom. / {holidays_assigned} fest.",
        f"{salud_emp_rate*100:.2f}%", f"{pension_emp_rate*100:.2f}%", f"{arl_rate*100:.3f}%", f"{caja_rate*100:.2f}%", f"{sena_rate*100:.2f}%", f"{icbf_rate*100:.2f}%", f"{prestaciones_rate*100:.2f}%",
        ""
    ],
    "Valor": [
        salary, bono_disponibilidad, bono_resultados, bono_comunicacion, valor_transporte,
        variable_bonus,
        ordinary_day_cost, ordinary_night_base_cost, night_surcharge_cost, extra_day_cost, extra_night_cost, sunday_cost + holiday_cost,
        salud_emp, pension_emp, arl_emp, caja_emp, sena_emp, icbf_emp, prestaciones,
        monthly_cost_one
    ]
})

breakdown_show = breakdown.copy()
breakdown_show["Valor"] = breakdown_show["Valor"].map(cop)
st.dataframe(breakdown_show, use_container_width=True, hide_index=True)

st.divider()
left, right = st.columns([1, 1])

with left:
    st.subheader("📊 Composición del costo")
    chart_data = breakdown[breakdown["Concepto"] != "TOTAL POR CONDUCTOR"].groupby("Bloque", as_index=False)["Valor"].sum()
    fig = px.pie(chart_data, names="Bloque", values="Valor", hole=0.45)
    st.plotly_chart(fig, use_container_width=True)

with right:
    st.subheader("📈 Horas estimadas")
    hours_df = pd.DataFrame({
        "Tipo": ["Diurnas ordinarias", "Nocturnas ordinarias", "Extras diurnas", "Extras nocturnas", "Dominicales", "Festivas"],
        "Horas": [ordinary_day_hours, ordinary_night_hours, extra_day_hours, extra_night_hours, sunday_hours, holiday_hours]
    })
    fig2 = px.bar(hours_df, x="Tipo", y="Horas", text="Horas")
    fig2.update_traces(texttemplate="%{text:,.1f}", textposition="outside")
    fig2.update_layout(xaxis_title="", yaxis_title="Horas", height=420)
    st.plotly_chart(fig2, use_container_width=True)

st.divider()
st.subheader(f"📅 Calendario operacional 14x7 - {month_name} {year}")
html = "<table style='width:100%; border-collapse:separate; border-spacing:7px;'>"
for week in sorted(df["Semana_mes"].unique()):
    html += "<tr>"
    week_data = df[df["Semana_mes"] == week]
    for _, r in week_data.iterrows():
        if r["Tipo_color"] == "DESCANSO":
            bg = "#D9D9D9"
        elif r["Tipo_color"] == "DOMINICAL":
            bg = "#F4CCCC"
        elif r["Tipo_color"] == "FESTIVO":
            bg = "#CFE2F3"
        elif r["Tipo_color"] == "NOCTURNO":
            bg = "#D9D2E9"
        else:
            bg = "#D9EAD3"
        cell = f"<div style='font-weight:700;font-size:16px'>{int(r['Dia'])}</div><div>{r['Dia_semana']}</div><div style='font-size:12px'>{r['Etiqueta']}</div><div style='font-size:12px'>D {r['Horas_diurnas']:.1f}h / N {r['Horas_nocturnas']:.1f}h</div>"
        html += f"<td style='background:{bg}; padding:10px; border-radius:12px; text-align:center; border:1px solid #ECECEC;'>{cell}</td>"
    html += "</tr>"
html += "</table>"
st.markdown(html, unsafe_allow_html=True)
st.caption("Verde: labora | Gris: descanso | Morado: nocturno | Rojo: dominical | Azul: festivo")

st.divider()
st.subheader("📋 Resumen semanal detallado")
weekly_rows = []
for week, group in df.groupby("Semana_mes"):
    h_total = group["Horas_totales"].sum()
    h_dia = group["Horas_diurnas"].sum()
    h_noc = group["Horas_nocturnas"].sum()
    h_ext_dia = group["Horas_extra_diurnas"].sum()
    h_ext_noc = group["Horas_extra_nocturnas"].sum()
    h_dom = group.loc[(group["Estado"] == "LABORA") & (group["Es_domingo"]), "Horas_totales"].sum()
    h_fes = group.loc[(group["Estado"] == "LABORA") & (group["Es_festivo"]), "Horas_totales"].sum()
    cost_week = (
        (h_dia * hour_value) +
        (h_noc * hour_value) +
        (h_noc * hour_value * night_rate) +
        (h_ext_dia * hour_value * (1 + extra_day_rate)) +
        (h_ext_noc * hour_value * (1 + extra_night_rate)) +
        (h_dom * hour_value * sunday_rate) +
        (h_fes * hour_value * holiday_rate)
    )
    weekly_rows.append({
        "Semana": f"Semana {week}",
        "Horas totales": h_total,
        "Horas diurnas": h_dia,
        "Horas nocturnas": h_noc,
        "Extras diurnas": h_ext_dia,
        "Extras nocturnas": h_ext_noc,
        "Horas dominicales": h_dom,
        "Horas festivas": h_fes,
        "Costo horas/recargos aprox.": cost_week
    })

weekly_df = pd.DataFrame(weekly_rows)
weekly_show = weekly_df.copy()
weekly_show["Costo horas/recargos aprox."] = weekly_show["Costo horas/recargos aprox."].map(cop)
st.dataframe(weekly_show, use_container_width=True, hide_index=True)

fig_week = px.bar(weekly_df, x="Semana", y="Costo horas/recargos aprox.", text="Costo horas/recargos aprox.")
fig_week.update_traces(texttemplate="%{text:,.0f}", textposition="outside")
fig_week.update_layout(xaxis_title="", yaxis_title="COP", height=380)
st.plotly_chart(fig_week, use_container_width=True)

st.divider()
st.subheader("📄 Detalle diario")
detail = df[[
    "Fecha", "Semana_mes", "Dia_semana", "Dia_ciclo_14x7", "Estado", "Etiqueta",
    "Horas_totales", "Horas_diurnas", "Horas_nocturnas",
    "Horas_ordinarias_diurnas", "Horas_ordinarias_nocturnas",
    "Horas_extra_diurnas", "Horas_extra_nocturnas", "Es_domingo", "Es_festivo"
]].copy()
st.dataframe(detail, use_container_width=True, hide_index=True)

csv = detail.to_csv(index=False).encode("utf-8-sig")
st.download_button("⬇️ Descargar detalle diario CSV", data=csv, file_name=f"detalle_14x7_{month_name}_{year}.csv", mime="text/csv")

st.warning("Proyección gerencial. Para liquidación oficial se debe validar naturaleza salarial/no salarial de bonos, clase de riesgo ARL, exoneraciones aplicables y normatividad vigente.")
