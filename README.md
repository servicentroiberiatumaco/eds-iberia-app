# EDS Servicentro Iberia — App de Control (Identidad Primax)

Digitalización de `1. PLANILLA ENERO IBERIA 2024 I.xlsx` en una app Streamlit + PostgreSQL
(Supabase), brandeada con los colores institucionales Primax, publicada permanentemente
en Streamlit Community Cloud.

## 1. Paleta aplicada
| Uso | Color | Hex |
|---|---|---|
| Botones / acentos | Naranja Primax | `#FF5B00` |
| Sidebar / encabezados / texto | Azul Marino | `#002855` |
| Alertas / KPIs secundarios | Amarillo Energía | `#FFC700` |
| Fondos | Blanco / Gris claro | `#FFFFFF` / `#F4F6F9` |

Configurado en `.streamlit/config.toml` (tema nativo de Streamlit) y reforzado con CSS
en `style.py` (sidebar azul, botones naranjas, tablas con encabezado azul, tarjetas de
alerta amarillas). Las gráficas usan Naranja=Gasolina y Azul=Diesel en todo el dashboard.

## 2. Esquema de base de datos (PostgreSQL)

**Catálogos maestros** (equivalentes a la pestaña `BD`):
- `bomberos(id, nombre, activo)`
- `turnos(id, nombre, activo)`
- `usuarios_creditos(id, nombre, saldo_inicial, activo)`
- `usuarios_prestamos(id, nombre, saldo_inicial, activo)`
- `descripcion_gastos(id, descripcion, activo)`
- `surtidores(id, surtidor_num, manguera, producto, activo)` — configuración física (3 surtidores, mangueras Diesel/Gasolina, igual a las hojas 01-31)

**Operación diaria** (equivalente a hojas `01`–`31`):
- `planillas(id, fecha, turno_id→turnos, bombero_id→bomberos, precio_gasolina, precio_diesel, efectivo, edenred, tarjetas_credito, sodexo_bonos, wiseo, faltante_sobrante, observaciones)` — un registro por turno/bombero/día, igual al bloque repetido en el Excel.
- `lecturas_surtidor(id, planilla_id→planillas, surtidor_id→surtidores, lectura_inicial, lectura_final, galones GENERATED)` — reemplaza las columnas "Lectura Inicial/Final/Ventas" por manguera.
- `gastos(id, planilla_id→planillas, descripcion_gasto_id→descripcion_gastos, fecha, valor, observaciones)`

**Cartera (nuevo módulo)**:
- `creditos_movimientos(id, usuario_credito_id→usuarios_creditos, planilla_id→planillas NULLABLE, fecha, tipo['credito'|'abono'], valor, observaciones)`
- `prestamos_movimientos(id, usuario_prestamo_id→usuarios_prestamos, planilla_id→planillas NULLABLE, fecha, tipo['prestamo'|'abono'], valor, observaciones)`

El **saldo pendiente** de cada usuario se calcula así (ver `database.saldos_creditos/saldos_prestamos`):
```
saldo_actual = saldo_inicial + Σ(nuevos créditos/préstamos) − Σ(abonos)
```
Este patrón de "ledger" (libro de movimientos) es el estándar para cuentas por cobrar:
nunca se sobrescribe un saldo, siempre se agregan movimientos y el saldo se deriva.
Así queda auditoría completa de quién otorgó/abonó qué y cuándo — igual a lo que pediste
("historial con saldo inicial, nuevos créditos, abonos y saldo pendiente").

Relaciones clave: `planillas 1—N lecturas_surtidor`, `planillas 1—N gastos`,
`planillas 1—N creditos_movimientos/prestamos_movimientos` (opcional, para trazar de qué
turno salió el crédito), `usuarios_creditos/usuarios_prestamos 1—N` sus respectivos movimientos.

## 3. Estructura de archivos entregados

```
primax_app/
├── .streamlit/
│   ├── config.toml                 # Tema Primax (colores nativos de Streamlit)
│   └── secrets.toml.example        # Plantilla de DATABASE_URL (copiar sin ".example")
├── .gitignore                      # Excluye secrets.toml real y __pycache__
├── database.py                     # Esquema PostgreSQL + toda la capa de datos
├── style.py                        # CSS de marca + helper de encabezados
├── Home.py                         # Dashboard/Analítica (página principal)
├── pages/
│   ├── 1_📝_Registro_Diario.py     # Captura diaria (reemplaza hojas 01-31)
│   ├── 2_💰_Creditos_y_Prestamos.py # Cartera: movimientos + alertas "quién debe"
│   ├── 3_📊_Reportes_Quincenales.py # Consolidado 1-15 / 16-fin + export Excel
│   └── 4_🗂️_Catalogos.py           # Mantenimiento de catálogos (pestaña BD)
└── requirements.txt
```

Streamlit detecta automáticamente los archivos en `pages/` y arma el menú lateral
(el emoji al inicio del nombre define el ícono; el número define el orden).

## 4. Base de datos: PostgreSQL en Supabase (persistencia real en la nube)

La app **ya no usa un archivo local** — se conecta a una base de datos PostgreSQL
gratuita alojada en Supabase, así que tus datos sobreviven a reinicios, redeploys y
se pueden usar desde cualquier computador simultáneamente.

### 4.1 Crear el proyecto gratuito en Supabase
1. Ve a [supabase.com](https://supabase.com) → **Start your project** → crea cuenta gratis.
2. **New project** → dale un nombre (ej. `eds-iberia`) → define una contraseña de base
   de datos segura y **guárdala**, la necesitarás → elige la región más cercana → **Create**.
3. Espera 1-2 minutos a que aprovisione el proyecto.
4. Ve a **Project Settings** (ícono de engranaje) → **Database** → sección **Connection string**
   → pestaña **URI**, modo **Session pooler** (recomendado para apps serverless como Streamlit Cloud).
5. Copia esa URL, tiene esta forma:
   ```
   postgresql://postgres.xxxxxxxxxxxx:[YOUR-PASSWORD]@aws-0-us-east-1.pooler.supabase.com:5432/postgres
   ```
6. Reemplaza `[YOUR-PASSWORD]` por la contraseña que definiste en el paso 2. Esta URL
   completa es tu `DATABASE_URL`.

### 4.2 Probar localmente (opcional pero recomendado)
1. Copia la plantilla:
   ```bash
   cp .streamlit/secrets.toml.example .streamlit/secrets.toml
   ```
2. Abre `.streamlit/secrets.toml` y pega tu `DATABASE_URL` real ahí.
3. Instala dependencias y corre:
   ```bash
   pip install -r requirements.txt
   streamlit run Home.py
   ```
4. La primera vez, la app crea sola las tablas en Supabase y precarga los catálogos
   base (bomberos, turnos, usuarios de crédito/préstamo, gastos, surtidores).
5. **Importante**: `.streamlit/secrets.toml` (el real, con tu contraseña) nunca se
   sube a GitHub — el `.gitignore` ya lo excluye. Solo se sube `secrets.toml.example`.

## 5. Publicar permanentemente en Streamlit Community Cloud (gratis)

### 5.1 Subir el código a GitHub
1. Crea una cuenta en [github.com](https://github.com) si no tienes.
2. Crea un repositorio nuevo (puede ser privado), ej. `eds-iberia-app`.
3. Sube el contenido de esta carpeta (`primax_app/`) a ese repositorio. Puedes hacerlo
   desde la web de GitHub ("Add file → Upload files") o con git:
   ```bash
   cd primax_app
   git init
   git add .
   git commit -m "App de control EDS Iberia"
   git branch -M main
   git remote add origin https://github.com/TU-USUARIO/eds-iberia-app.git
   git push -u origin main
   ```
   Verifica que `secrets.toml` (el real) **no** quedó incluido — solo debe verse
   `secrets.toml.example` en GitHub.

### 5.2 Desplegar en Streamlit Community Cloud
1. Ve a [share.streamlit.io](https://share.streamlit.io) e inicia sesión con tu cuenta de GitHub.
2. **Create app** → **Deploy a public app from GitHub** (o el tipo de app que ofrezca).
3. Selecciona tu repositorio `eds-iberia-app`, rama `main`, y como **Main file path**
   escribe `Home.py`.
4. Antes de darle a Deploy, abre **Advanced settings** → sección **Secrets** → pega:
   ```toml
   DATABASE_URL = "postgresql://postgres.xxxxxxxxxxxx:TU-PASSWORD@aws-0-us-east-1.pooler.supabase.com:5432/postgres"
   ```
   (tu URL real de Supabase del paso 4.1).
5. Clic en **Deploy**. En 1-3 minutos tu app queda publicada en una URL tipo
   `https://eds-iberia-app.streamlit.app` — accesible desde cualquier computador o
   celular con internet, sin instalar nada.
6. Comparte esa URL con quien deba usar la app (bomberos, administración, etc.).

### 5.3 Actualizaciones futuras
Cualquier cambio que subas a la rama `main` en GitHub se redespliega automáticamente
en la misma URL — sin perder datos, porque estos viven en Supabase, no en el servidor
de la app.

## 6. Flujo de uso diario (ya con la app publicada)
- Entra a la URL de tu app (ej. `https://eds-iberia-app.streamlit.app`) desde cualquier
  computador o celular.
- Ve a **Registro Diario** → llena fecha, turno, bombero, lecturas de cada manguera,
  medios de pago (efectivo/Edenred/tarjetas/Sodexo/Wiseo), faltante/sobrante, y
  opcionalmente un gasto/crédito/préstamo del turno → **Guardar planilla**.
- Para movimientos adicionales de cartera (abonos, créditos nuevos fuera de una
  planilla) usa **Créditos y Préstamos**.
- Revisa **Reportes Quincenales** para ver el consolidado 1-15 / 16-fin de mes /
  mensual, igual que tus hojas `1er/2do Reporte Quincenal` y `Reporte Mensual`, con
  botón para exportar a `.xlsx`.
- El **Dashboard** (Home) trae los KPIs, tendencias de combustible, gastos vs.
  ingresos y evolución de cartera, con filtro por rango de fechas o por año.
- **Respaldo**: aunque los datos ya viven en Supabase (persistentes), puedes exportar
  respaldos periódicos desde **Project Settings → Database → Backups** en el panel de Supabase.

## 7. Notas de diseño / decisiones tomadas

- El Excel original repite tres bloques "PLANILLA" por hoja (uno por bombero/turno);
  esto se modeló como **una fila en `planillas` por bloque**, lo cual permite filtrar,
  sumar y graficar sin depender de la posición en la hoja.
- Los "surtidores" del Excel real no son simétricos (Surtidor 1 tiene 2 mangueras,
  Surtidores 2 y 3 tienen 4); por eso `surtidores` es una tabla configurable en vez de
  columnas fijas — puedes agregar/quitar mangueras desde **Catálogos** si cambia la
  estación.
- Todo saldo de cartera es **calculado, no almacenado**, evitando inconsistencias
  cuando se edite el historial.
- Los nombres de páginas usan emoji + número para que el menú de Streamlit quede
  ordenado y visualmente alineado a la operación (Registro → Cartera → Reportes → Catálogos).

## 8. Próximos pasos sugeridos (fuera de este alcance)
- Autenticación de usuarios (Streamlit soporta `st.login`/OIDC o `streamlit-authenticator`)
  para que cada bombero/administrador entre con su propio usuario.
- Botón de "editar planilla" (hoy el formulario solo crea; para editar se puede
  añadir un selector de planilla existente y precargar sus valores).
- Si el negocio crece y el tráfico supera el free tier de Supabase (500MB de BD,
  pausas por inactividad tras 1 semana sin uso en el plan gratuito), se puede subir
  a su plan Pro sin cambiar una línea de código de la app.
