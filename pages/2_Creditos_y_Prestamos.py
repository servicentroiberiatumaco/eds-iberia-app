import streamlit as st
import pandas as pd
import datetime as dt
import database as db
from style import inject_css, header

st.set_page_config(page_title="Créditos y Préstamos | Iberia", page_icon="💰", layout="wide")
inject_css()
db.init_db()
db.seed_if_empty()

header("💰 Créditos y Préstamos", "Cuentas por cobrar: saldo inicial, movimientos y saldo pendiente")

tab_cred, tab_prest, tab_alertas = st.tabs(["Usuarios Crédito", "Usuarios Préstamo", "🔔 ¿Quién debe?"])

# ---------------- CREDITOS ----------------
with tab_cred:
    st.subheader("Registrar movimiento de crédito")
    usuarios = db.fetch_catalogo("usuarios_creditos")
    if not usuarios:
        st.warning("No hay usuarios de crédito. Agrégalos en Catálogos.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        uid = c1.selectbox("Usuario", options=[u["id"] for u in usuarios],
                            format_func=lambda i: next(u["nombre"] for u in usuarios if u["id"] == i), key="cu")
        tipo = c2.selectbox("Tipo de movimiento", ["credito", "abono"], key="ct",
                             format_func=lambda t: "Nuevo crédito" if t == "credito" else "Abono")
        valor = c3.number_input("Valor", min_value=0.0, step=1000.0, key="cv")
        fecha = c4.date_input("Fecha", value=dt.date.today(), format="DD/MM/YYYY", key="cf")
        obs = st.text_input("Observaciones", key="cobs")
        if st.button("Guardar movimiento de crédito"):
            if valor > 0:
                db.registrar_movimiento_credito(uid, None, str(fecha), tipo, valor, obs)
                st.success("Movimiento registrado.")
                st.rerun()
            else:
                st.error("El valor debe ser mayor a 0.")

    st.divider()
    st.subheader("Historial y saldo por usuario")
    saldos = pd.DataFrame(db.saldos_creditos())
    if not saldos.empty:
        st.dataframe(
            saldos.rename(columns={"nombre": "Usuario", "saldo_inicial": "Saldo Inicial",
                                    "total_credito": "Créditos Otorgados", "total_abonos": "Abonos",
                                    "saldo_actual": "Saldo Pendiente"}),
            use_container_width=True, hide_index=True
        )
    else:
        st.info("Sin datos aún.")

# ---------------- PRESTAMOS ----------------
with tab_prest:
    st.subheader("Registrar movimiento de préstamo")
    usuariosp = db.fetch_catalogo("usuarios_prestamos")
    if not usuariosp:
        st.warning("No hay usuarios de préstamo. Agrégalos en Catálogos.")
    else:
        c1, c2, c3, c4 = st.columns(4)
        uid = c1.selectbox("Usuario", options=[u["id"] for u in usuariosp],
                            format_func=lambda i: next(u["nombre"] for u in usuariosp if u["id"] == i), key="pu")
        tipo = c2.selectbox("Tipo de movimiento", ["prestamo", "abono"], key="pt",
                             format_func=lambda t: "Nuevo préstamo" if t == "prestamo" else "Abono")
        valor = c3.number_input("Valor", min_value=0.0, step=1000.0, key="pv")
        fecha = c4.date_input("Fecha", value=dt.date.today(), format="DD/MM/YYYY", key="pf")
        obs = st.text_input("Observaciones", key="pobs")
        if st.button("Guardar movimiento de préstamo"):
            if valor > 0:
                db.registrar_movimiento_prestamo(uid, None, str(fecha), tipo, valor, obs)
                st.success("Movimiento registrado.")
                st.rerun()
            else:
                st.error("El valor debe ser mayor a 0.")

    st.divider()
    st.subheader("Historial y saldo por usuario")
    saldosp = pd.DataFrame(db.saldos_prestamos())
    if not saldosp.empty:
        st.dataframe(
            saldosp.rename(columns={"nombre": "Usuario", "saldo_inicial": "Saldo Inicial",
                                     "total_prestamo": "Préstamos Otorgados", "total_abonos": "Abonos",
                                     "saldo_actual": "Saldo Pendiente"}),
            use_container_width=True, hide_index=True
        )
    else:
        st.info("Sin datos aún.")

# ---------------- ALERTAS ----------------
with tab_alertas:
    st.subheader("🔔 Reporte rápido: cuánto debe cada quién")
    saldos = pd.DataFrame(db.saldos_creditos())
    saldosp = pd.DataFrame(db.saldos_prestamos())
    total_pend_c = saldos[saldos.saldo_actual > 0]["saldo_actual"].sum() if not saldos.empty else 0
    total_pend_p = saldosp[saldosp.saldo_actual > 0]["saldo_actual"].sum() if not saldosp.empty else 0
    m1, m2, m3 = st.columns(3)
    m1.metric("Cartera crédito pendiente", f"${total_pend_c:,.0f}")
    m2.metric("Cartera préstamo pendiente", f"${total_pend_p:,.0f}")
    m3.metric("Total por cobrar", f"${(total_pend_c + total_pend_p):,.0f}")

    if not saldos.empty:
        pend = saldos[saldos.saldo_actual > 0].sort_values("saldo_actual", ascending=False)
        if not pend.empty:
            st.markdown("**Créditos pendientes:**")
            for _, r in pend.iterrows():
                st.markdown(f"<div class='primax-alert'>🧾 <b>{r['nombre']}</b> debe "
                             f"<b>${r['saldo_actual']:,.0f}</b></div>", unsafe_allow_html=True)
    if not saldosp.empty:
        pendp = saldosp[saldosp.saldo_actual > 0].sort_values("saldo_actual", ascending=False)
        if not pendp.empty:
            st.markdown("**Préstamos pendientes:**")
            for _, r in pendp.iterrows():
                st.markdown(f"<div class='primax-alert'>💵 <b>{r['nombre']}</b> debe "
                             f"<b>${r['saldo_actual']:,.0f}</b></div>", unsafe_allow_html=True)
    if (saldos.empty or (saldos.saldo_actual <= 0).all()) and (saldosp.empty or (saldosp.saldo_actual <= 0).all()):
        st.success("No hay saldos pendientes registrados. 🎉")
