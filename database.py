"""
database.py
Capa de acceso a datos para la app EDS Servicentro Iberia (Primax).
Backend: PostgreSQL (Supabase, free tier) para persistencia real en la nube.

La cadena de conexion se lee, en este orden:
1. st.secrets["DATABASE_URL"]  (usado en Streamlit Community Cloud)
2. variable de entorno DATABASE_URL (uso local / pruebas)
"""

import os
import streamlit as st
import psycopg2
import psycopg2.extras
from contextlib import contextmanager


def _get_database_url():
    try:
        if "DATABASE_URL" in st.secrets:
            return st.secrets["DATABASE_URL"]
    except Exception:
        pass
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "No se encontró DATABASE_URL. Configúrala en .streamlit/secrets.toml "
            "(local) o en 'Secrets' del panel de Streamlit Community Cloud (producción)."
        )
    return url


class ConnWrapper:
    """Envoltorio delgado sobre una conexión psycopg2 para que el resto del código
    pueda seguir llamando conn.execute(...) igual que hacía con sqlite3."""

    def __init__(self, pg_conn):
        self._conn = pg_conn

    def execute(self, query, params=()):
        cur = self._conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur.execute(query, params)
        return cur

    def executemany(self, query, seq_of_params):
        cur = self._conn.cursor()
        cur.executemany(query, seq_of_params)
        return cur

    def executescript(self, script):
        cur = self._conn.cursor()
        cur.execute(script)
        return cur

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()


@contextmanager
def get_conn():
    pg_conn = psycopg2.connect(_get_database_url())
    wrapper = ConnWrapper(pg_conn)
    try:
        yield wrapper
        wrapper.commit()
    finally:
        wrapper.close()


SCHEMA = """
CREATE TABLE IF NOT EXISTS bomberos (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL UNIQUE,
    activo INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS turnos (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL UNIQUE,
    activo INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS usuarios_creditos (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL UNIQUE,
    saldo_inicial REAL NOT NULL DEFAULT 0,
    activo INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS usuarios_prestamos (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL UNIQUE,
    saldo_inicial REAL NOT NULL DEFAULT 0,
    activo INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS descripcion_gastos (
    id SERIAL PRIMARY KEY,
    descripcion TEXT NOT NULL UNIQUE,
    activo INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS surtidores (
    id SERIAL PRIMARY KEY,
    surtidor_num INTEGER NOT NULL,
    manguera TEXT NOT NULL,
    producto TEXT NOT NULL CHECK (producto IN ('Gasolina','Diesel')),
    activo INTEGER NOT NULL DEFAULT 1,
    UNIQUE(surtidor_num, manguera)
);

CREATE TABLE IF NOT EXISTS planillas (
    id SERIAL PRIMARY KEY,
    fecha DATE NOT NULL,
    turno_id INTEGER REFERENCES turnos(id),
    bombero_id INTEGER REFERENCES bomberos(id),
    precio_gasolina REAL NOT NULL DEFAULT 0,
    precio_diesel REAL NOT NULL DEFAULT 0,
    efectivo REAL NOT NULL DEFAULT 0,
    edenred REAL NOT NULL DEFAULT 0,
    tarjetas_credito REAL NOT NULL DEFAULT 0,
    sodexo_bonos REAL NOT NULL DEFAULT 0,
    wiseo REAL NOT NULL DEFAULT 0,
    faltante_sobrante REAL NOT NULL DEFAULT 0,
    observaciones TEXT,
    creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS lecturas_surtidor (
    id SERIAL PRIMARY KEY,
    planilla_id INTEGER NOT NULL REFERENCES planillas(id) ON DELETE CASCADE,
    surtidor_id INTEGER NOT NULL REFERENCES surtidores(id),
    lectura_inicial REAL NOT NULL DEFAULT 0,
    lectura_final REAL NOT NULL DEFAULT 0,
    galones REAL GENERATED ALWAYS AS (lectura_final - lectura_inicial) STORED,
    UNIQUE(planilla_id, surtidor_id)
);

CREATE TABLE IF NOT EXISTS creditos_movimientos (
    id SERIAL PRIMARY KEY,
    usuario_credito_id INTEGER NOT NULL REFERENCES usuarios_creditos(id),
    planilla_id INTEGER REFERENCES planillas(id) ON DELETE SET NULL,
    fecha DATE NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('credito','abono')),
    valor REAL NOT NULL,
    observaciones TEXT
);

CREATE TABLE IF NOT EXISTS prestamos_movimientos (
    id SERIAL PRIMARY KEY,
    usuario_prestamo_id INTEGER NOT NULL REFERENCES usuarios_prestamos(id),
    planilla_id INTEGER REFERENCES planillas(id) ON DELETE SET NULL,
    fecha DATE NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('prestamo','abono')),
    valor REAL NOT NULL,
    observaciones TEXT
);

CREATE TABLE IF NOT EXISTS gastos (
    id SERIAL PRIMARY KEY,
    planilla_id INTEGER NOT NULL REFERENCES planillas(id) ON DELETE CASCADE,
    descripcion_gasto_id INTEGER NOT NULL REFERENCES descripcion_gastos(id),
    fecha DATE NOT NULL,
    valor REAL NOT NULL,
    observaciones TEXT
);
"""


def init_db():
    with get_conn() as conn:
        conn.executescript(SCHEMA)


def seed_if_empty():
    with get_conn() as conn:
        count = conn.execute("SELECT COUNT(*) c FROM bomberos").fetchone()["c"]
        if count > 0:
            return

        bomberos = ["Bryan Lugo", "Raul Martinez", "Julio Quiñonez", "Alexis Arroyo",
                    "Diego Quiñonez", "Urbano Solis"]
        turnos = ["05:00am - 01:00pm", "01:00pm - 08:00pm", "06:00am - 08:00pm"]
        gastos_desc = ["Aptos bucanero", "Gastos Casa 1er Turno", "Gastos Casa 2do Turno",
                       "quincena", "finca", "PROFESORES NENES HELLEN", "vigilante",
                       "CORPONARIÑO SAN JUAN", "Grua", "HONORARIOS", "DIFERENCIA",
                       "NICOLAS E. M.", "KIA", "CENTRO MEDICO TUMACO", "FELIX HENAO"]
        usuarios_creditos = ["REDES Y EDIFICACIONES", "karen marin", "AERONAUTICA CIVIL",
                              "RAMIRO ZAMBRANO", "MALARIA", "INPEC", "ONORIO HERNANDEZ",
                              "AERONAUTICA BOMBEROS", "Fiscalia", "Montagas", "Pedro Zambrano",
                              "GUARDACOSTA", "COBRA - MOVISTAR", "CONELTEC", "ANDRES GARCIA",
                              "William Basantes", "POLICIA ANTICIPO", "DRILLING",
                              "batallon infanteri de marina", "TRANS TURISMO ANDINO",
                              "JAIRO CORTES"]
        usuarios_prestamos = ["Raul", "Diego", "Brayan", "Alexis", "Julio", "Nino", "Shay",
                               "Hellen", "Karen", "Parmenio", "Esperanza", "Anita",
                               "Sandra Segura", "YESICA ARBOLEDA", "BETTY", "VENUS E",
                               "CORPONARIÑO SAN JUAN", "JAURO SEGOVIA"]
        surtidores = [
            (1, "Manguera 1", "Diesel"), (1, "Manguera 2", "Gasolina"),
            (2, "Manguera 1", "Diesel"), (2, "Manguera 2", "Diesel"),
            (2, "Manguera 3", "Gasolina"), (2, "Manguera 4", "Gasolina"),
            (3, "Manguera 1", "Diesel"), (3, "Manguera 2", "Diesel"),
            (3, "Manguera 3", "Gasolina"), (3, "Manguera 4", "Gasolina"),
        ]

        conn.executemany("INSERT INTO bomberos(nombre) VALUES (%s) ON CONFLICT (nombre) DO NOTHING", [(b,) for b in bomberos])
        conn.executemany("INSERT INTO turnos(nombre) VALUES (%s) ON CONFLICT (nombre) DO NOTHING", [(t,) for t in turnos])
        conn.executemany("INSERT INTO descripcion_gastos(descripcion) VALUES (%s) ON CONFLICT (descripcion) DO NOTHING", [(g,) for g in gastos_desc])
        conn.executemany("INSERT INTO usuarios_creditos(nombre) VALUES (%s) ON CONFLICT (nombre) DO NOTHING", [(u,) for u in usuarios_creditos])
        conn.executemany("INSERT INTO usuarios_prestamos(nombre) VALUES (%s) ON CONFLICT (nombre) DO NOTHING", [(u,) for u in usuarios_prestamos])
        conn.executemany(
            "INSERT INTO surtidores(surtidor_num, manguera, producto) VALUES (%s,%s,%s) ON CONFLICT (surtidor_num, manguera) DO NOTHING",
            surtidores
        )


# ---------- Helpers genericos de catalogo ----------

def fetch_catalogo(tabla, solo_activos=True):
    q = f"SELECT * FROM {tabla}"
    if solo_activos:
        q += " WHERE activo = 1"
    q += " ORDER BY nombre" if tabla != "surtidores" else " ORDER BY surtidor_num, manguera"
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(q).fetchall()]


def add_catalogo_item(tabla, nombre):
    with get_conn() as conn:
        conn.execute(f"INSERT INTO {tabla}(nombre) VALUES (%s) ON CONFLICT (nombre) DO NOTHING", (nombre,))


def set_catalogo_activo(tabla, item_id, activo):
    with get_conn() as conn:
        conn.execute(f"UPDATE {tabla} SET activo = %s WHERE id = %s", (int(activo), item_id))


# ---------- Planillas ----------

def crear_planilla(fecha, turno_id, bombero_id, precio_gasolina, precio_diesel,
                    efectivo, edenred, tarjetas_credito, sodexo_bonos, wiseo,
                    faltante_sobrante, observaciones=""):
    with get_conn() as conn:
        cur = conn.execute("""
            INSERT INTO planillas (fecha, turno_id, bombero_id, precio_gasolina, precio_diesel,
                efectivo, edenred, tarjetas_credito, sodexo_bonos, wiseo, faltante_sobrante, observaciones)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id
        """, (fecha, turno_id, bombero_id, precio_gasolina, precio_diesel,
              efectivo, edenred, tarjetas_credito, sodexo_bonos, wiseo, faltante_sobrante, observaciones))
        return cur.fetchone()["id"]


def guardar_lectura_surtidor(planilla_id, surtidor_id, lectura_inicial, lectura_final):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO lecturas_surtidor (planilla_id, surtidor_id, lectura_inicial, lectura_final)
            VALUES (%s,%s,%s,%s)
            ON CONFLICT(planilla_id, surtidor_id) DO UPDATE SET
                lectura_inicial = excluded.lectura_inicial,
                lectura_final = excluded.lectura_final
        """, (planilla_id, surtidor_id, lectura_inicial, lectura_final))


def registrar_gasto(planilla_id, descripcion_gasto_id, fecha, valor, observaciones=""):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO gastos (planilla_id, descripcion_gasto_id, fecha, valor, observaciones)
            VALUES (%s,%s,%s,%s,%s)
        """, (planilla_id, descripcion_gasto_id, fecha, valor, observaciones))


def registrar_movimiento_credito(usuario_id, planilla_id, fecha, tipo, valor, observaciones=""):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO creditos_movimientos (usuario_credito_id, planilla_id, fecha, tipo, valor, observaciones)
            VALUES (%s,%s,%s,%s,%s,%s)
        """, (usuario_id, planilla_id, fecha, tipo, valor, observaciones))


def registrar_movimiento_prestamo(usuario_id, planilla_id, fecha, tipo, valor, observaciones=""):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO prestamos_movimientos (usuario_prestamo_id, planilla_id, fecha, tipo, valor, observaciones)
            VALUES (%s,%s,%s,%s,%s,%s)
        """, (usuario_id, planilla_id, fecha, tipo, valor, observaciones))


# ---------- Consultas de reporte ----------

def ventas_por_producto(fecha_ini, fecha_fin):
    q = """
    SELECT p.fecha, s.producto,
           SUM(l.galones) AS galones,
           SUM(l.galones * CASE WHEN s.producto='Gasolina' THEN p.precio_gasolina ELSE p.precio_diesel END) AS valor_venta
    FROM lecturas_surtidor l
    JOIN planillas p ON p.id = l.planilla_id
    JOIN surtidores s ON s.id = l.surtidor_id
    WHERE p.fecha BETWEEN %s AND %s
    GROUP BY p.fecha, s.producto
    ORDER BY p.fecha
    """
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(q, (fecha_ini, fecha_fin)).fetchall()]


def gastos_vs_ingresos(fecha_ini, fecha_fin):
    q_ingresos = """
        SELECT fecha, SUM(efectivo+edenred+tarjetas_credito+sodexo_bonos+wiseo) AS ingresos
        FROM planillas WHERE fecha BETWEEN %s AND %s GROUP BY fecha
    """
    q_gastos = """
        SELECT fecha, SUM(valor) AS gastos FROM gastos WHERE fecha BETWEEN %s AND %s GROUP BY fecha
    """
    with get_conn() as conn:
        ingresos = {str(r["fecha"]): r["ingresos"] for r in conn.execute(q_ingresos, (fecha_ini, fecha_fin))}
        gastos = {str(r["fecha"]): r["gastos"] for r in conn.execute(q_gastos, (fecha_ini, fecha_fin))}
    fechas = sorted(set(ingresos) | set(gastos))
    return [{"fecha": f, "ingresos": ingresos.get(f, 0) or 0, "gastos": gastos.get(f, 0) or 0} for f in fechas]


def saldos_creditos():
    q = """
    SELECT u.id, u.nombre, u.saldo_inicial,
           COALESCE(SUM(CASE WHEN m.tipo='credito' THEN m.valor ELSE 0 END),0) AS total_credito,
           COALESCE(SUM(CASE WHEN m.tipo='abono' THEN m.valor ELSE 0 END),0) AS total_abonos
    FROM usuarios_creditos u
    LEFT JOIN creditos_movimientos m ON m.usuario_credito_id = u.id
    WHERE u.activo = 1
    GROUP BY u.id, u.nombre, u.saldo_inicial
    ORDER BY u.nombre
    """
    with get_conn() as conn:
        rows = [dict(r) for r in conn.execute(q).fetchall()]
    for r in rows:
        r["saldo_actual"] = r["saldo_inicial"] + r["total_credito"] - r["total_abonos"]
    return rows


def saldos_prestamos():
    q = """
    SELECT u.id, u.nombre, u.saldo_inicial,
           COALESCE(SUM(CASE WHEN m.tipo='prestamo' THEN m.valor ELSE 0 END),0) AS total_prestamo,
           COALESCE(SUM(CASE WHEN m.tipo='abono' THEN m.valor ELSE 0 END),0) AS total_abonos
    FROM usuarios_prestamos u
    LEFT JOIN prestamos_movimientos m ON m.usuario_prestamo_id = u.id
    WHERE u.activo = 1
    GROUP BY u.id, u.nombre, u.saldo_inicial
    ORDER BY u.nombre
    """
    with get_conn() as conn:
        rows = [dict(r) for r in conn.execute(q).fetchall()]
    for r in rows:
        r["saldo_actual"] = r["saldo_inicial"] + r["total_prestamo"] - r["total_abonos"]
    return rows


def evolucion_cartera(fecha_ini, fecha_fin):
    q_cred = """
        SELECT fecha, tipo, SUM(valor) v FROM creditos_movimientos
        WHERE fecha BETWEEN %s AND %s GROUP BY fecha, tipo
    """
    q_pre = """
        SELECT fecha, tipo, SUM(valor) v FROM prestamos_movimientos
        WHERE fecha BETWEEN %s AND %s GROUP BY fecha, tipo
    """
    with get_conn() as conn:
        creditos = [dict(r) for r in conn.execute(q_cred, (fecha_ini, fecha_fin))]
        prestamos = [dict(r) for r in conn.execute(q_pre, (fecha_ini, fecha_fin))]
    return creditos, prestamos


def planillas_en_rango(fecha_ini, fecha_fin):
    q = """
    SELECT p.*, b.nombre AS bombero, t.nombre AS turno
    FROM planillas p
    LEFT JOIN bomberos b ON b.id = p.bombero_id
    LEFT JOIN turnos t ON t.id = p.turno_id
    WHERE p.fecha BETWEEN %s AND %s
    ORDER BY p.fecha, p.id
    """
    with get_conn() as conn:
        return [dict(r) for r in conn.execute(q, (fecha_ini, fecha_fin)).fetchall()]
