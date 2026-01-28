# 🤖 finanzasBot 2.0 — Asistente financiero personal (Telegram)

finanzasBot 2.0 es un **asistente financiero personal** diseñado para **una sola persona**, enfocado en **prevención, control y claridad**, no en contabilidad tradicional.

El objetivo del proyecto es reducir errores financieros comunes (olvidos, saturación, uso excesivo de tarjeta) mediante **reglas simples**, **carriles claros** y **decisiones anticipadas**.

> ❌ No es un contador  
> ❌ No optimiza impuestos  
> ❌ No hace proyecciones complejas  
> ✅ Ayuda a no generar intereses  
> ✅ Reduce carga mental  
> ✅ Prioriza decisiones simples y oportunas  

---

## 🧠 Filosofía del proyecto

- **El banco manda**  
  El estado de cuenta (EDC) es la fuente de verdad. El bot no infiere ni recalcula deuda.

- **Prevención > análisis histórico**  
  El foco está en el riesgo futuro (uso post-corte), no en la deuda pasada.

- **Python decide, la IA explica**  
  Toda la lógica financiera se calcula en Python.  
  La IA solo traduce números a acciones humanas.

- **UX > perfección financiera**  
  Menos datos, menos decisiones, menos ansiedad.

---

## 🎯 Qué hace el bot

- Lleva control de:
  - 💳 Tarjeta BBVA (uso post-corte vs techo)
  - 📦 Sobres mensuales obligatorios
  - 💵 Efectivo / débito
- Genera un **resumen diario claro** (`/resumen`)
- Analiza **gastos necesarios vs ocio**
- Construye un **contexto mínimo** para la IA
- Devuelve **acciones concretas**, no teoría financiera (`/plan`)

---

## 🚫 Qué NO hace el bot

- No lee PDFs bancarios
- No scrapea bancos
- No infiere MSI
- No mezcla deuda histórica con riesgo futuro
- No guarda memoria en la IA
- No toma decisiones por el usuario

---

## 📂 Estructura del proyecto

```text
finanzasBot/
├── bot.py                  # Orquestador del bot de Telegram
├── resumen.py              # Genera texto de resumen (no calcula)
├── calculos.py             # Cálculos financieros básicos
├── clasificador_gastos.py  # Clasificación de gastos (necesario / ocio)
├── analizador_bbva.py      # Uso BBVA post-corte vs techo
├── bbva_estado.py          # Adaptador BBVA para IA
├── ia_contexto.py          # Construcción del contexto mínimo para IA
├── edc.py                  # Estados de cuenta (snapshots)
├── storage.py              # Lectura/escritura de CSV
├── movimientos.csv         # Base histórica de movimientos
├── edc_snapshots.csv       # Snapshots de estados de cuenta
├── config.json             # Reglas del sistema (sobres, ingresos, tarjetas)
├── .env                    # Credenciales (Telegram, OpenAI)
└── requirements.txt
💳 Modelo financiero (resumen)
Ingresos
Principalmente quincenales

Día 15 → cubrir sobres

Día 30 → reservar para pago BBVA del 27 siguiente

Sobres mensuales (obligatorios)
Se pagan completos

No se prorratean

No son gasto opcional

Ejemplo:

{
  "carro": 2000,
  "pension": 1200,
  "mama": 500
}
Tarjeta BBVA
Corte: día 7

Pago límite: día 27

Uso permitido: del 8 al 7

Techo de consumo post-corte (prevención)

🤖 Uso de IA (importante)
La IA NO:

calcula

decide montos

infiere fechas

guarda memoria

modifica datos

La IA SÍ:

traduce números a acciones claras

prioriza riesgos

explica consecuencias

da máximo 5 acciones concretas

Cada llamada a la IA es stateless (sin memoria).

🧪 Estado actual del proyecto
✔ Bot funcional
✔ Control de BBVA activo
✔ Resumen limpio y accionable
✔ Clasificación de gastos
✔ Contexto mínimo para IA
✔ Arquitectura modular y auditable

🚧 Próximas ideas (no todas implementadas)
Alertas automáticas 🟡 / 🔴

Objetivos opcionales (ej. ocio máximo)

Comparación entre periodos

Visualización simple

Más reglas de prevención

⚠️ Nota final
Este proyecto está fuertemente personalizado al flujo financiero del autor.
No pretende ser genérico ni comercial.

Si lo adaptas, ajusta primero las reglas, no el código.
