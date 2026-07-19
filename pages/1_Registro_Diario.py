import streamlit as st
import datetime as dt
import database as db
from style import inject_css, header

st.set_page_config(page_title="Registro Diario | Iberia", page_icon="📝", layout="wide")
inject_css()
db.init_db()
db.seed_if_empty()

header("📝 Registro Diario de Planilla", "Equivalente a las hojas 01-31 del Excel: un formulario por turno/bombero")

bomberos = db.fetch_catalogo("bomberos")
turnos = db.fetch_catalogo("turnos")
surtidores = db.fetch_catalogo("surtidores")
gastos_desc = db.fetch_catalogo("descripcion_gastos")
usuarios_creditos = db.fetch_catalogo("usuarios_creditos")
usuarios_prestamos = db.fetch_catalogo("usuarios_prestamos")

if not bomberos or not turnos:
    st.warning("Primero registra bomberos y turnos en la página Catálogos.")
    st.stop()

with st.form("form_planilla", clear_on_submit=False):
    c1, c2, c3 = st.columns(3)
    fecha = c1.date_input("Fecha", value=dt.date.today(), format="DD/MM/YYYY")
    turno_id = c2.selectbox("Turno", options=[t["id"] for t in turnos],
                             format_func=lambda i: next(t["nombre"] for t in turnos if t["id"] == i))
    bombero_id = c3.selectbox("Bombero", options=[b["id"] for b in bomberos],
                               format_func=lambda i: next(b["nombre"] for b in bomberos if b["id"] == i))

    c4, c5 = st.columns(2)
    precio_gasolina = c4.number_input("Precio galón Gasolina", min_value=0.0, value=13320.0, step=10.0)
    precio_diesel = c5.number_input("Precio galón Diesel", min_value=0.0, value=9170.0, step=10.0)

    st.markdown("#### Lecturas por surtidor / manguera")
    lecturas = {}
    cols = st.columns(2)
    for idx, s in enumerate(surtidores):
        with cols[idx % 2]:
            st.caption(f"Surtidor {s['surtidor_num']} · {s['manguera']} · {s['producto']}")
            li = st.number_input(f"Lectura inicial ({s['manguera']} S{s['surtidor_num']})",
                                  min_value=0.0, key=f"li_{s['id']}")
            lf = st.number_input(f"Lectura final ({s['manguera']} S{s['surtidor_num']})",
                                  min_value=0.0, key=f"lf_{s['id']}")
            lecturas[s["id"]] = (li, lf)

    st.markdown("#### Registro de bomberos (medios de pago)")
    p1, p2, p3, p4, p5 = st.columns(5)
    efectivo = p1.number_input("Efectivo", min_value=0.0, step=1000.0)
    edenred = p2.number_input("Edenred", min_value=0.0, step=1000.0)
    tarjetas = p3.number_input("Tarjetas Crédito", min_value=0.0, step=1000.0)
    sodexo = p4.number_input("Sodexo Bonos", min_value=0.0, step=1000.0)
    wiseo = p5.number_input("Wiseo", min_value=0.0, step=1000.0)

    faltante_sobrante = st.number_input("Faltante / Sobrante", step=100.0, format="%.2f")
    observaciones = st.text_area("Observaciones", height=68)

    st.markdown("#### Gastos del turno (opcional)")
    gcols = st.columns(3)
    gasto_desc_id = gcols[0].selectbox("Descripción gasto", options=[0] + [g["id"] for g in gastos_desc],
                                        format_func=lambda i: "—" if i == 0 else next(g["descripcion"] for g in gastos_desc if g["id"] == i))
    gasto_valor = gcols[1].number_input("Valor gasto", min_value=0.0, step=1000.0)
    gasto_obs = gcols[2].text_input("Obs. gasto")

    st.markdown("#### Crédito otorgado en el turno (opcional)")
    ccols = st.columns(3)
    credito_usuario_id = ccols[0].selectbox("Usuario crédito", options=[0] + [u["id"] for u in usuarios_creditos],
                                             format_func=lambda i: "—" if i == 0 else next(u["nombre"] for u in usuarios_creditos if u["id"] == i))
    credito_valor = ccols[1].number_input("Valor crédito", min_value=0.0, step=1000.0)
    credito_obs = ccols[2].text_input("Obs. crédito")

    st.markdown("#### Préstamo otorgado en el turno (opcional)")
    pcols = st.columns(3)
    prestamo_usuario_id = pcols[0].selectbox("Usuario préstamo", options=[0] + [u["id"] for u in usuarios_prestamos],
                                              format_func=lambda i: "—" if i == 0 else next(u["nombre"] for u in usuarios_prestamos if u["id"] == i))
    prestamo_valor = pcols[1].number_input("Valor préstamo", min_value=0.0, step=1000.0)
    prestamo_obs = pcols[2].text_input("Obs. préstamo")

    submitted = st.form_submit_button("💾 Guardar planilla")

if submitted:
    planilla_id = db.crear_planilla(
        str(fecha), turno_id, bombero_id, precio_gasolina, precio_diesel,
        efectivo, edenred, tarjetas, sodexo, wiseo, faltante_sobrante, observaciones
    )
    for surtidor_id, (li, lf) in lecturas.items():
        db.guardar_lectura_surtidor(planilla_id, surtidor_id, li, lf)
    if gasto_desc_id and gasto_valor > 0:
        db.registrar_gasto(planilla_id, gasto_desc_id, str(fecha), gasto_valor, gasto_obs)
    if credito_usuario_id and credito_valor > 0:
        db.registrar_movimiento_credito(credito_usuario_id, planilla_id, str(fecha), "credito", credito_valor, credito_obs)
    if prestamo_usuario_id and prestamo_valor > 0:
        db.registrar_movimiento_prestamo(prestamo_usuario_id, planilla_id, str(fecha), "prestamo", prestamo_valor, prestamo_obs)
    st.success(f"Planilla guardada correctamente (ID {planilla_id}).")

st.divider()
st.markdown("### Planillas registradas (último mes)")
hoy = dt.date.today()
rows = db.planillas_en_rango(str(hoy.replace(day=1)), str(hoy))
if rows:
    import pandas as pd
    df = pd.DataFrame(rows)[["id", "fecha", "turno", "bombero", "efectivo", "edenred",
                              "tarjetas_credito", "sodexo_bonos", "wiseo", "faltante_sobrante"]]
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.info("Aún no hay planillas este mes.")
