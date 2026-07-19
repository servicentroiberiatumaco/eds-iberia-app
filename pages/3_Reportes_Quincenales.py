import streamlit as st
import pandas as pd
import datetime as dt
import database as db
from style import inject_css, header, NARANJA, AZUL

st.set_page_config(page_title="Reportes Quincenales | Iberia", page_icon="📊", layout="wide")
inject_css()
db.init_db()
db.seed_if_empty()

header("📊 Reportes Quincenales y Mensuales", "Consolidado automático 1-15 / 16-fin de mes, igual que el Excel")

hoy = dt.date.today()
c1, c2 = st.columns(2)
anio = c1.number_input("Año", value=hoy.year, step=1)
mes = c2.selectbox("Mes", list(range(1, 13)), index=hoy.month - 1,
                    format_func=lambda m: dt.date(2000, m, 1).strftime("%B").capitalize())

import calendar
ultimo_dia = calendar.monthrange(anio, mes)[1]
q1_ini, q1_fin = dt.date(anio, mes, 1), dt.date(anio, mes, 15)
q2_ini, q2_fin = dt.date(anio, mes, 16), dt.date(anio, mes, ultimo_dia)


def render_reporte(fecha_ini, fecha_fin, titulo):
    st.markdown(f"#### {titulo} ({fecha_ini.strftime('%d/%m')} al {fecha_fin.strftime('%d/%m')})")
    fi, ff = str(fecha_ini), str(fecha_fin)
    ventas = pd.DataFrame(db.ventas_por_producto(fi, ff))
    planillas = pd.DataFrame(db.planillas_en_rango(fi, ff))

    if ventas.empty:
        st.info("Sin ventas registradas en este rango.")
    else:
        resumen = ventas.groupby("producto")[["galones", "valor_venta"]].sum().reset_index()
        st.dataframe(resumen.rename(columns={"producto": "Producto", "galones": "Galones",
                                              "valor_venta": "Valor Venta"}),
                     use_container_width=True, hide_index=True)
        total_gal = resumen["galones"].sum()
        total_val = resumen["valor_venta"].sum()
        st.markdown(f"**TOTAL VENTA COMBUSTIBLE:** {total_gal:,.0f} gal · ${total_val:,.0f}")

    if not planillas.empty:
        medios = planillas[["efectivo", "edenred", "tarjetas_credito", "sodexo_bonos", "wiseo"]].sum()
        st.markdown("**Registro de bomberos (medios de pago):**")
        medios_df = medios.rename({"efectivo": "Efectivo", "edenred": "Edenred",
                                    "tarjetas_credito": "Tarjetas Crédito", "sodexo_bonos": "Sodexo Bonos",
                                    "wiseo": "Wiseo"}).reset_index()
        medios_df.columns = ["Item", "Valor"]
        st.dataframe(medios_df, use_container_width=True, hide_index=True)
        st.markdown(f"**TOTAL:** ${medios.sum():,.0f}")
    else:
        st.info("Sin planillas registradas en este rango.")


t1, t2, t3 = st.tabs(["1ra Quincena (1-15)", "2da Quincena (16-fin)", "Reporte Mensual"])
with t1:
    render_reporte(q1_ini, q1_fin, "1er Reporte Quincenal")
with t2:
    render_reporte(q2_ini, q2_fin, "2do Reporte Quincenal")
with t3:
    render_reporte(dt.date(anio, mes, 1), dt.date(anio, mes, ultimo_dia), "Reporte Mensual")

st.divider()
st.markdown("### Exportar a Excel")
if st.button("Generar archivo .xlsx del mes seleccionado"):
    fi, ff = str(dt.date(anio, mes, 1)), str(dt.date(anio, mes, ultimo_dia))
    planillas = pd.DataFrame(db.planillas_en_rango(fi, ff))
    ventas = pd.DataFrame(db.ventas_por_producto(fi, ff))
    path = f"/tmp/reporte_{anio}_{mes:02d}.xlsx"
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        (planillas if not planillas.empty else pd.DataFrame()).to_excel(writer, sheet_name="Planillas", index=False)
        (ventas if not ventas.empty else pd.DataFrame()).to_excel(writer, sheet_name="Ventas", index=False)
    with open(path, "rb") as f:
        st.download_button("⬇️ Descargar reporte", f, file_name=f"reporte_{anio}_{mes:02d}.xlsx")
