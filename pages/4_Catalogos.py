import streamlit as st
import pandas as pd
import database as db
from style import inject_css, header

st.set_page_config(page_title="Catálogos | Iberia", page_icon="🗂️", layout="wide")
inject_css()
db.init_db()
db.seed_if_empty()

header("🗂️ Catálogos Maestros (BD)", "Equivalente a la pestaña BD: Usuarios Créditos, Préstamos, Bomberos, Turnos, Gastos")

CATALOGOS = {
    "Bomberos": "bomberos",
    "Turnos": "turnos",
    "Usuarios Créditos": "usuarios_creditos",
    "Usuarios Préstamos": "usuarios_prestamos",
    "Descripción de Gastos": "descripcion_gastos",
}

tabs = st.tabs(list(CATALOGOS.keys()) + ["Surtidores"])

for tab, (label, tabla) in zip(tabs[:-1], CATALOGOS.items()):
    with tab:
        c1, c2 = st.columns([3, 1])
        nuevo = c1.text_input(f"Nuevo registro en {label}", key=f"new_{tabla}")
        if c2.button("Agregar", key=f"add_{tabla}") and nuevo.strip():
            db.add_catalogo_item(tabla, nuevo.strip())
            st.success(f"'{nuevo}' agregado.")
            st.rerun()

        items = db.fetch_catalogo(tabla, solo_activos=False)
        if items:
            df = pd.DataFrame(items)
            cols = [c for c in ["id", "nombre", "saldo_inicial", "activo"] if c in df.columns]
            st.dataframe(df[cols], use_container_width=True, hide_index=True)

            desactivar_id = st.selectbox(f"Activar/Desactivar en {label}", options=[i["id"] for i in items],
                                          format_func=lambda i: next(x["nombre"] for x in items if x["id"] == i),
                                          key=f"tog_{tabla}")
            item_actual = next(x for x in items if x["id"] == desactivar_id)
            nuevo_estado = not bool(item_actual["activo"])
            if st.button(f"{'Activar' if nuevo_estado else 'Desactivar'}", key=f"togbtn_{tabla}"):
                db.set_catalogo_activo(tabla, desactivar_id, nuevo_estado)
                st.rerun()
        else:
            st.info("Sin registros aún.")

with tabs[-1]:
    st.markdown("Configuración física de surtidores y mangueras (Diesel/Gasolina) según la planilla original.")
    surtidores = db.fetch_catalogo("surtidores", solo_activos=False)
    if surtidores:
        st.dataframe(pd.DataFrame(surtidores), use_container_width=True, hide_index=True)
    c1, c2, c3 = st.columns(3)
    num = c1.number_input("N° Surtidor", min_value=1, step=1, key="sn")
    manguera = c2.text_input("Manguera (ej. Manguera 1)", key="sm")
    producto = c3.selectbox("Producto", ["Diesel", "Gasolina"], key="sp")
    if st.button("Agregar surtidor/manguera"):
        with db.get_conn() as conn:
            conn.execute(
                "INSERT INTO surtidores(surtidor_num, manguera, producto) VALUES (%s,%s,%s) "
                "ON CONFLICT (surtidor_num, manguera) DO NOTHING",
                (num, manguera, producto)
            )
        st.success("Surtidor agregado.")
        st.rerun()
