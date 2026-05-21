
import calendar
from datetime import date, datetime, time, timedelta
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Costo conductor + vehículo 14x7", page_icon="🚐", layout="wide")
st.title("🚐 Simulador costo conductor + vehículo 14x7")
st.caption("Proyección gerencial: costo empresa, costos del vehículo y neto a pagar al conductor.")

MESES={"Enero":1,"Febrero":2,"Marzo":3,"Abril":4,"Mayo":5,"Junio":6,"Julio":7,"Agosto":8,"Septiembre":9,"Octubre":10,"Noviembre":11,"Diciembre":12}

def cop(v): return f"${round(float(v)):,}".replace(",", ".")
def hrs(v): return f"{round(float(v)):,} h".replace(",", ".")
def tarifa_dom(a): return 100 if a>=2027 else (90 if a==2026 else 80)

def rango(inicio, fin):
    b=datetime(2026,1,1); i=datetime.combine(b,inicio); f=datetime.combine(b,fin)
    if f<=i: f+=timedelta(days=1)
    return (f-i).total_seconds()/3600, i, f

def partir(inicio, fin):
    total,i,f=rango(inicio,fin); cur=i; paso=timedelta(minutes=15); dia=noc=0
    while cur<f:
        sig=min(cur+paso,f); h=(sig-cur).total_seconds()/3600; t=cur.time()
        if t>=time(19,0) or t<time(6,0): noc+=h
        else: dia+=h
        cur=sig
    return round(dia,2),round(noc,2),round(total,2)

def calendario(anio,mes,ciclo_ini,h_ini,h_fin,h_ord,festivos_manual):
    dias=calendar.monthrange(anio,mes)[1]
    h_dia_turno,h_noc_turno,h_total_turno=partir(h_ini,h_fin)
    filas=[]; ciclo=ciclo_ini; festivos=0
    for d in range(1,dias+1):
        f=date(anio,mes,d); dc=((ciclo-1)%21)+1; trabaja=dc<=14; domingo=f.weekday()==6
        festivo=False
        if trabaja and not domingo and festivos<festivos_manual:
            festivo=True; festivos+=1
        ht=h_total_turno if trabaja else 0
        hd=h_dia_turno if trabaja else 0
        hn=h_noc_turno if trabaja else 0
        he=max(0,ht-h_ord)
        pd=hd/ht if ht else 0; pn=hn/ht if ht else 0
        hed=he*pd; hen=he*pn; hod=max(0,hd-hed); hon=max(0,hn-hen)
        if not trabaja: et,col="DESCANSO","#D9D9D9"
        elif festivo: et,col="FESTIVO","#CFE2F3"
        elif domingo: et,col="DOMINICAL","#F4CCCC"
        elif hn>0: et,col="LABORA / NOCT.","#D9D2E9"
        else: et,col="LABORA","#D9EAD3"
        filas.append({"Fecha":f,"Día":d,"Semana":((d-1)//7)+1,"Día_semana":["Lun","Mar","Mié","Jue","Vie","Sáb","Dom"][f.weekday()],
        "Día_ciclo_14x7":dc,"Estado":"LABORA" if trabaja else "DESCANSO","Etiqueta":et,"Color":col,"Es_domingo":domingo,"Es_festivo":festivo,
        "Horas_totales":ht,"Horas_diurnas":hd,"Horas_nocturnas":hn,"Horas_ordinarias_diurnas":hod,"Horas_ordinarias_nocturnas":hon,
        "Horas_extra_diurnas":hed,"Horas_extra_nocturnas":hen})
        ciclo+=1
    return pd.DataFrame(filas)

with st.sidebar:
    st.header("⚙️ Escenario")
    anio=st.number_input("Año",2025,2035,2026)
    mes_nombre=st.selectbox("Mes",list(MESES.keys()),index=4)
    mes=MESES[mes_nombre]
    conductores=st.number_input("Cantidad de conductores",1,500,1)
    ciclo_ini=st.slider("Día ciclo 14x7 al iniciar mes",1,21,1)

    st.divider(); st.subheader("🕐 Jornada / disponibilidad")
    h_ini=st.time_input("Hora inicio",value=time(3,0),step=1800)
    h_fin=st.time_input("Hora finalización",value=time(15,0),step=1800)
    horas_disponibles=st.number_input("Horas disponibles por día",1.0,15.0,12.0,step=0.5)
    h_ord=st.number_input("Horas ordinarias base día",1.0,12.0,8.0,step=0.5)
    limite_fatiga=st.number_input("Límite máximo fatiga",1.0,24.0,15.0,step=0.5)

    st.divider(); st.subheader("💰 Base salarial")
    smlv=st.number_input("SMLV / salario base",0,value=1750905,step=10000)
    bono_disp=st.number_input("Bono disponibilidad",0,value=214000,step=10000)
    bono_res=st.number_input("Bono resultados",0,value=240492,step=10000)
    bono_com=st.number_input("Bono comunicación",0,value=30000,step=5000)
    transporte=st.number_input("Valor transporte",0,value=0,step=10000)

    st.divider(); st.subheader("🎯 Comisión productividad")
    produccion=st.number_input("Producción vehículo",0,value=16000000,step=100000)
    meta=st.number_input("Meta mínima para comisión",0,value=16000000,step=100000)
    pct_com=st.slider("% comisión sobre producción",0.0,10.0,2.0,0.5)/100
    comision=produccion*pct_com if produccion>=meta else 0

    st.divider(); st.subheader("📌 Recargos")
    rec_noc=st.number_input("Recargo nocturno %",0,200,35)/100
    rec_ext_dia=st.number_input("Extra diurna %",0,200,25)/100
    rec_ext_noc=st.number_input("Extra nocturna %",0,200,75)/100
    rec_dom=st.number_input("Dominical %",0,200,tarifa_dom(anio))/100
    rec_fes=st.number_input("Festivo %",0,200,tarifa_dom(anio))/100
    festivos_mes=st.number_input("Festivos laborados mes",0,10,0)

    st.divider(); st.subheader("🧾 Prestaciones y aportes empresa")
    prima=st.number_input("Prima %",0.0,20.0,8.33,step=0.01)/100
    ces=st.number_input("Cesantías %",0.0,20.0,8.33,step=0.01)/100
    int_ces=st.number_input("Interés cesantías %",0.0,10.0,1.0,step=0.01)/100
    vac=st.number_input("Vacaciones %",0.0,20.0,4.17,step=0.01)/100
    pen_emp=st.number_input("Pensión empresa %",0.0,30.0,12.0,step=0.01)/100
    ccp=st.number_input("CCP/Caja %",0.0,20.0,4.0,step=0.01)/100
    arl=st.number_input("ARL %",0.0,20.0,6.96,step=0.01)/100
    salud_emp=st.number_input("Salud empresa %",0.0,20.0,8.5,step=0.01)/100
    sena=st.number_input("SENA %",0.0,10.0,0.0,step=0.01)/100
    icbf=st.number_input("ICBF %",0.0,10.0,0.0,step=0.01)/100
    fsp=st.number_input("FSP %",0.0,10.0,0.0,step=0.01)/100

    st.divider(); st.subheader("💵 Descuentos conductor")
    salud_empdo=st.number_input("Salud empleado %",0.0,20.0,4.0,step=0.1)/100
    pension_empdo=st.number_input("Pensión empleado %",0.0,20.0,4.0,step=0.1)/100
    otros_desc=st.number_input("Otros descuentos",0,value=0,step=10000)

    st.divider(); st.subheader("🚐 Costos vehículo/operación")
    dotacion=st.number_input("Dotación",0,value=0,step=10000)
    alimentacion=st.number_input("Alimentación",0,value=0,step=10000)
    lavado=st.number_input("Lavado general vehículo",0,value=0,step=10000)
    estadia=st.number_input("Estadía",0,value=0,step=10000)
    peaje=st.number_input("Peaje con chip",0,value=0,step=10000)
    combustible=st.number_input("Combustible",0,value=0,step=10000)
    parqueadero=st.number_input("Parqueadero",0,value=0,step=10000)
    mantenimiento=st.number_input("Mantenimiento",0,value=0,step=10000)

df=calendario(anio,mes,ciclo_ini,h_ini,h_fin,h_ord,int(festivos_mes))
h_total_dia,_,_=rango(h_ini,h_fin)
base_salarial=smlv+bono_res+bono_disp
valor_hora=base_salarial/220 if base_salarial else 0

h_dia=df["Horas_diurnas"].sum(); h_noc=df["Horas_nocturnas"].sum()
h_ord_dia=df["Horas_ordinarias_diurnas"].sum(); h_ord_noc=df["Horas_ordinarias_nocturnas"].sum()
h_ext_dia=df["Horas_extra_diurnas"].sum(); h_ext_noc=df["Horas_extra_nocturnas"].sum()
h_dom=df.loc[(df["Estado"]=="LABORA")&(df["Es_domingo"]),"Horas_totales"].sum()
h_fes=df.loc[(df["Estado"]=="LABORA")&(df["Es_festivo"]),"Horas_totales"].sum()
domingos=int(((df["Estado"]=="LABORA")&(df["Es_domingo"])).sum())
festivos=int(((df["Estado"]=="LABORA")&(df["Es_festivo"])).sum())

c_rec_noc=h_noc*valor_hora*rec_noc
c_ext_dia=h_ext_dia*valor_hora*(1+rec_ext_dia)
c_ext_noc=h_ext_noc*valor_hora*(1+rec_ext_noc)
c_dom=h_dom*valor_hora*rec_dom
c_fes=h_fes*valor_hora*rec_fes
c_recargos=c_rec_noc+c_ext_dia+c_ext_noc+c_dom+c_fes

devengado=smlv+bono_disp+bono_res+bono_com+transporte+comision+c_recargos

prestaciones={
"Prima":base_salarial*prima,"Cesantías":base_salarial*ces,"Interés cesantías":base_salarial*int_ces,"Vacaciones":base_salarial*vac}
aportes={
"Pensión empresa":base_salarial*pen_emp,"CCP/Caja":base_salarial*ccp,"ARL":base_salarial*arl,
"Salud empresa":base_salarial*salud_emp,"SENA":base_salarial*sena,"ICBF":base_salarial*icbf,"FSP":base_salarial*fsp}
total_prest=sum(prestaciones.values()); total_aportes=sum(aportes.values())

desc_salud=base_salarial*salud_empdo; desc_pension=base_salarial*pension_empdo
total_desc=desc_salud+desc_pension+otros_desc
neto=devengado-total_desc

costos_veh={
"Dotación":dotacion,"Alimentación":alimentacion,"Lavado general vehículo":lavado,"Estadía":estadia,
"Peaje con chip":peaje,"Combustible":combustible,"Parqueadero":parqueadero,"Mantenimiento":mantenimiento}
total_veh=sum(costos_veh.values())

costo_conductor=devengado+total_prest+total_aportes
costo_conductor_veh=costo_conductor+total_veh
costo_flota=costo_conductor_veh*conductores
costo_anual=costo_flota*12
ratio=costo_conductor_veh/neto if neto else 0

st.subheader("📌 Resultado principal")
a,b,c,d=st.columns(4)
a.metric("Costo conductor + vehículo",cop(costo_conductor_veh))
b.metric("Neto a pagar conductor",cop(neto))
c.metric("Costo total mensual flota",cop(costo_flota))
d.metric("Costo anual proyectado",cop(costo_anual))
e,f,g,h=st.columns(4)
e.metric("Base salarial",cop(base_salarial))
f.metric("Horas diurnas",hrs(h_dia))
g.metric("Horas nocturnas",hrs(h_noc))
h.metric("Empresa paga por cada $1 neto",f"${ratio:.2f}")

if h_total_dia>limite_fatiga: st.error(f"⚠️ Fatiga: {hrs(h_total_dia)} supera límite {hrs(limite_fatiga)}")
else: st.success(f"✅ Jornada dentro del límite de fatiga: {hrs(h_total_dia)} / {hrs(limite_fatiga)}")
if horas_disponibles>12: st.warning("⚠️ Horas disponibles superiores a 12. Validar tratamiento como extras/disponibilidad especial.")
else: st.info("ℹ️ Horas disponibles dentro del máximo operativo de 12.")

st.divider()
st.subheader("💵 Qué le llega al conductor")
neto_df=pd.DataFrame({"Concepto":["SMLV","Bono disponibilidad","Bono resultados","Bono comunicación","Transporte","Comisión productividad","Recargos/extras/dominicales","Descuento salud","Descuento pensión","Otros descuentos","NETO A PAGAR"],
"Valor":[smlv,bono_disp,bono_res,bono_com,transporte,comision,c_recargos,-desc_salud,-desc_pension,-otros_desc,neto]})
neto_df["Valor"]=neto_df["Valor"].map(cop)
st.dataframe(neto_df,use_container_width=True,hide_index=True)

st.divider()
st.subheader("🏢 Costo empresa: conductor + vehículo")
rows=[]
rows += [("CONDUCTOR","Devengado bruto",devengado),("CONDUCTOR","Base salarial usada",base_salarial),("CONDUCTOR","Recargos/extras/dominicales",c_recargos),("CONDUCTOR","Comisión productividad",comision)]
for k,v in prestaciones.items(): rows.append(("PRESTACIONES",k,v))
for k,v in aportes.items(): rows.append(("SEGURIDAD/APORTES",k,v))
for k,v in costos_veh.items(): rows.append(("VEHÍCULO",k,v))
rows.append(("TOTAL","COSTO TOTAL CONDUCTOR + VEHÍCULO",costo_conductor_veh))
costos=pd.DataFrame(rows,columns=["Bloque","Concepto","Valor"])
costos_show=costos.copy(); costos_show["Valor"]=costos_show["Valor"].map(cop)
st.dataframe(costos_show,use_container_width=True,hide_index=True)

st.subheader("📊 Composición costo empresa")
st.bar_chart(costos[costos["Bloque"]!="TOTAL"].groupby("Bloque")["Valor"].sum())

st.divider()
st.subheader("⏱️ Resumen de horas")
horas_df=pd.DataFrame({"Tipo":["Diurnas ordinarias","Nocturnas ordinarias","Extras diurnas","Extras nocturnas","Dominicales","Festivas"],
"Horas":[round(h_ord_dia),round(h_ord_noc),round(h_ext_dia),round(h_ext_noc),round(h_dom),round(h_fes)]})
st.dataframe(horas_df,use_container_width=True,hide_index=True)
st.bar_chart(horas_df.set_index("Tipo"))

st.divider()
st.subheader(f"📅 Calendario operacional 14x7 - {mes_nombre} {anio}")
html="<table style='width:100%; border-collapse:separate; border-spacing:7px;'>"
for sem in sorted(df["Semana"].unique()):
    html+="<tr>"
    for _,r in df[df["Semana"]==sem].iterrows():
        celda=f"<div style='font-weight:700;font-size:16px'>{int(r['Día'])}</div><div>{r['Día_semana']}</div><div style='font-size:12px'>{r['Etiqueta']}</div><div style='font-size:12px'>D {round(r['Horas_diurnas'])}h / N {round(r['Horas_nocturnas'])}h</div>"
        html+=f"<td style='background:{r['Color']}; padding:10px; border-radius:12px; text-align:center; border:1px solid #ECECEC;'>{celda}</td>"
    html+="</tr>"
html+="</table>"
st.markdown(html,unsafe_allow_html=True)

st.divider()
st.subheader("📋 Resumen semanal")
weekly=[]
for sem,gp in df.groupby("Semana"):
    wd=gp["Horas_diurnas"].sum(); wn=gp["Horas_nocturnas"].sum(); wed=gp["Horas_extra_diurnas"].sum(); wen=gp["Horas_extra_nocturnas"].sum()
    wdom=gp.loc[(gp["Estado"]=="LABORA")&(gp["Es_domingo"]),"Horas_totales"].sum()
    wfes=gp.loc[(gp["Estado"]=="LABORA")&(gp["Es_festivo"]),"Horas_totales"].sum()
    costo=(wd*valor_hora)+(wn*valor_hora)+(wn*valor_hora*rec_noc)+(wed*valor_hora*(1+rec_ext_dia))+(wen*valor_hora*(1+rec_ext_noc))+(wdom*valor_hora*rec_dom)+(wfes*valor_hora*rec_fes)
    weekly.append({"Semana":f"Semana {sem}","Horas totales":round(gp["Horas_totales"].sum()),"Horas diurnas":round(wd),"Horas nocturnas":round(wn),"Extras diurnas":round(wed),"Extras nocturnas":round(wen),"Horas dominicales":round(wdom),"Horas festivas":round(wfes),"Costo horas/recargos aprox.":cop(costo)})
st.dataframe(pd.DataFrame(weekly),use_container_width=True,hide_index=True)

st.divider()
st.subheader("📄 Detalle diario")
detalle=df[["Fecha","Semana","Día_semana","Día_ciclo_14x7","Estado","Etiqueta","Horas_totales","Horas_diurnas","Horas_nocturnas","Horas_ordinarias_diurnas","Horas_ordinarias_nocturnas","Horas_extra_diurnas","Horas_extra_nocturnas","Es_domingo","Es_festivo"]].copy()
for col in ["Horas_totales","Horas_diurnas","Horas_nocturnas","Horas_ordinarias_diurnas","Horas_ordinarias_nocturnas","Horas_extra_diurnas","Horas_extra_nocturnas"]:
    detalle[col]=detalle[col].round(0).astype(int)
st.dataframe(detalle,use_container_width=True,hide_index=True)
st.download_button("⬇️ Descargar detalle diario CSV",data=detalle.to_csv(index=False).encode("utf-8-sig"),file_name=f"detalle_conductor_vehiculo_{mes_nombre}_{anio}.csv",mime="text/csv")
st.warning("Proyección gerencial. Validar con el área laboral/contable: bonos salariales, ARL real, viáticos, exoneraciones y tratamiento tributario.")
