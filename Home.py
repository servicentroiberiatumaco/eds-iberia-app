import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import datetime as dt

import database as db
from style import inject_css, header, NARANJA, AZUL, AMARILLO

st.set_page_config(page_title="EDS Iberia | Primax", page_icon="⛽", layout="wide")
inject_css()
db.init_db()
db.seed_if_empty()

header("⛽ EDS Servicentro Iberia", "Dashboard de Control - Estilo Primax")

# ---------------- Filtros ----------------
c1, c2, c3 = st.columns([1, 1, 2])
with c1:
    modo = st.selectbox("Agrupar por", ["Rango de fechas", "Año"])
with c2:
    hoy = dt.date.today()
if modo == "Rango de fechas":
    with c3:
        rango = st.date_input("Rango", value=(hoy.replace(day=1), hoy), format="DD/MM/YYYY")
    if isinstance(rango, tuple) and len(rango) == 2:
        fecha_ini, fecha_fin = rango
    else:
        fecha_ini, fecha_fin = hoy.replace(day=1), hoy
else:
    with c3:
        anio = st.number_input("Año", value=hoy.year, step=1)
    fecha_ini, fecha_fin = dt.date(anio, 1, 1), dt.date(anio, 12, 31)

fi, ff = str(fecha_ini), str(fecha_fin)

# ---------------- KPIs ----------------
ventas = pd.DataFrame(db.ventas_por_producto(fi, ff))
gxi = pd.DataFrame(db.gastos_vs_ingresos(fi, ff))
saldos_c = pd.DataFrame(db.saldos_creditos())
saldos_p = pd.DataFrame(db.saldos_prestamos())

total_galones = ventas["galones"].sum() if not ventas.empty else 0
total_venta = ventas["valor_venta"].sum() if not ventas.empty else 0
total_ingresos = gxi["ingresos"].sum() if not gxi.empty else 0
total_gastos = gxi["gastos"].sum() if not gxi.empty else 0
cartera_creditos = saldos_c["saldo_actual"].sum() if not saldos_c.empty else 0
cartera_prestamos = saldos_p["saldo_actual"].sum() if not saldos_p.empty else 0

k1, k2, k3, k4, k5 = st.columns(5)
k1.metric("Galones vendidos", f"{total_galones:,.0f}")
k2.metric("Venta total ($)", f"${total_venta:,.0f}")
k3.metric("Ingresos ($)", f"${total_ingresos:,.0f}")
k4.metric("Gastos ($)", f"${total_gastos:,.0f}")
k5.metric("Cartera pendiente ($)", f"${(cartera_creditos + cartera_prestamos):,.0f}")

st.divider()

# ---------------- Grafica: tendencia de ventas combustible ----------------
col1, col2 = st.columns(2)
with col1:
    st.subheader("Tendencia de ventas de combustible")
    if not ventas.empty:
        fig = px.line(ventas, x="fecha", y="galones", color="producto", markers=True,
                       color_discrete_map={"Gasolina": NARANJA, "Diesel": AZUL})
        fig.update_layout(plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
                           font_color=AZUL, legend_title_text="Producto")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay datos de ventas registrados en este rango todavía.")

with col2:
    st.subheader("Venta en $ por producto")
    if not ventas.empty:
        fig2 = px.bar(ventas, x="fecha", y="valor_venta", color="producto", barmode="group",
                       color_discrete_map={"Gasolina": NARANJA, "Diesel": AZUL})
        fig2.update_layout(plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF",
                            font_color=AZUL, legend_title_text="Producto")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("No hay datos de ventas registrados en este rango todavía.")

# ---------------- Gastos vs Ingresos ----------------
st.subheader("Gastos frente a ingresos")
if not gxi.empty:
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(x=gxi["fecha"], y=gxi["ingresos"], name="Ingresos", marker_color=AZUL))
    fig3.add_trace(go.Bar(x=gxi["fecha"], y=gxi["gastos"], name="Gastos", marker_color=NARANJA))
    fig3.update_layout(barmode="group", plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF", font_color=AZUL)
    st.plotly_chart(fig3, use_container_width=True)
else:
    st.info("No hay datos de gastos/ingresos en este rango todavía.")

# ---------------- Cartera de creditos ----------------
st.subheader("Comportamiento de la cartera (créditos y préstamos)")
creditos_mov, prestamos_mov = db.evolucion_cartera(fi, ff)
dfc = pd.DataFrame(creditos_mov)
dfp = pd.DataFrame(prestamos_mov)
if not dfc.empty or not dfp.empty:
    fig4 = go.Figure()
    if not dfc.empty:
        otorg = dfc[dfc.tipo == "credito"]
        recaud = dfc[dfc.tipo == "abono"]
        fig4.add_trace(go.Scatter(x=otorg.fecha, y=otorg.v, name="Créditos otorgados",
                                   line=dict(color=AZUL), mode="lines+markers"))
        fig4.add_trace(go.Scatter(x=recaud.fecha, y=recaud.v, name="Créditos recaudados",
                                   line=dict(color=AMARILLO), mode="lines+markers"))
    if not dfp.empty:
        otorgp = dfp[dfp.tipo == "prestamo"]
        recaudp = dfp[dfp.tipo == "abono"]
        fig4.add_trace(go.Scatter(x=otorgp.fecha, y=otorgp.v, name="Préstamos otorgados",
                                   line=dict(color=NARANJA), mode="lines+markers"))
        fig4.add_trace(go.Scatter(x=recaudp.fecha, y=recaudp.v, name="Préstamos recaudados",
                                   line=dict(color="#7A7A7A"), mode="lines+markers"))
    fig4.update_layout(plot_bgcolor="#FFFFFF", paper_bgcolor="#FFFFFF", font_color=AZUL)
    st.plotly_chart(fig4, use_container_width=True)
else:
    st.info("No hay movimientos de cartera en este rango todavía.")

st.divider()

# ---------------- Alertas: quien debe ----------------
st.subheader("🔔 ¿Cuánto debe cada quién? (saldo pendiente actual)")
tab1, tab2 = st.tabs(["Créditos", "Préstamos"])
with tab1:
    if not saldos_c.empty:
        pendientes = saldos_c[saldos_c.saldo_actual != 0].sort_values("saldo_actual", ascending=False)
        st.dataframe(pendientes[["nombre", "saldo_inicial", "total_credito", "total_abonos", "saldo_actual"]]
                     .rename(columns={"nombre": "Usuario", "saldo_inicial": "Saldo Inicial",
                                       "total_credito": "Créditos", "total_abonos": "Abonos",
                                       "saldo_actual": "Saldo Pendiente"}),
                     use_container_width=True, hide_index=True)
    else:
        st.info("Sin usuarios de crédito registrados aún.")
with tab2:
    if not saldos_p.empty:
        pendientesp = saldos_p[saldos_p.saldo_actual != 0].sort_values("saldo_actual", ascending=False)
        st.dataframe(pendientesp[["nombre", "saldo_inicial", "total_prestamo", "total_abonos", "saldo_actual"]]
                     .rename(columns={"nombre": "Usuario", "saldo_inicial": "Saldo Inicial",
                                       "total_prestamo": "Préstamos", "total_abonos": "Abonos",
                                       "saldo_actual": "Saldo Pendiente"}),
                     use_container_width=True, hide_index=True)
    else:
        st.info("Sin usuarios de préstamo registrados aún.")

st.caption("Usa el menú lateral para ir a Registro Diario, Créditos y Préstamos, Catálogos o Reportes Quincenales.")
