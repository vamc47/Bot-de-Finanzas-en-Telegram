import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from datetime import date
from analizador_bbva import obtener_uso_bbva_desde_corte
from bbva_estado import construir_estado_bbva
from parser_edc import parsear_edc_texto
from edc import registrar_edc, obtener_edc_activo
from clasificador_gastos import resumir_gastos
from ia_contexto import construir_input_ia
from calculos import calcular_efectivo
hoy = date.today().isoformat()
from storage import init_csv, guardar_movimiento, leer_movimientos
from calculos import (
    calcular_totales,
    calcular_saldos_por_cuenta,
    evaluar_sobres_mensuales,
    calcular_tarjeta_bbva,
    calcular_tarjeta_plata
)
from resumen import resumen_completo

# 🔐 Cargar llaves
load_dotenv()
TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)


if not TOKEN:
    raise ValueError("❌ No se encontró TELEGRAM_TOKEN en .env")

# 📂 Cargar configuración financiera
with open("config.json", "r", encoding="utf-8") as f:
    CONFIG = json.load(f)


def fecha_ultimo_corte_bbva(hoy=None):
    hoy = hoy or date.today()

    if hoy.day >= 7:
        return date(hoy.year, hoy.month, 7)
    else:
        if hoy.month == 1:
            return date(hoy.year - 1, 12, 7)
        return date(hoy.year, hoy.month - 1, 7)
    

# 🤖 Comando /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🤖 Bot financiero activo")

# 💰 Ingreso
async def ingreso(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        monto = float(context.args[0])
        categoria = context.args[1].lower()
        cuenta = context.args[2].lower() if len(context.args) > 2 else "efectivo"

        guardar_movimiento("ingreso", monto, categoria, cuenta)
        await update.message.reply_text("✅ Ingreso registrado")

    except Exception:
        await update.message.reply_text(
            "Uso correcto:\n/ingreso monto categoria [cuenta]"
        )

# 💸 Gasto
async def gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        monto = float(context.args[0])
        categoria = context.args[1].lower()
        cuenta = context.args[2].lower() if len(context.args) > 2 else "efectivo"

        guardar_movimiento("gasto", monto, categoria, cuenta)
        await update.message.reply_text("✅ Gasto registrado")

    except Exception:
        await update.message.reply_text(
            "Uso correcto:\n/gasto monto categoria [cuenta]"
        )

# 💳 Pago
async def pago(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        monto = float(context.args[0])
        categoria = context.args[1].lower()
        cuenta = context.args[2].lower() if len(context.args) > 2 else "efectivo"

        guardar_movimiento("pago", monto, categoria, cuenta)
        await update.message.reply_text("✅ Pago registrado")

    except Exception:
        await update.message.reply_text(
            "Uso correcto:\n/pago monto categoria [cuenta]"
        )

# 📊 Resumen
async def resumen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    movs = leer_movimientos()

    totales = calcular_totales(movs)
    saldos = calcular_saldos_por_cuenta(movs)
    sobres = evaluar_sobres_mensuales(
        movs, CONFIG["sobres_mensuales"]
    )

    # 🔹 NUEVO MODELO BBVA
    edc_bbva = obtener_edc_activo("bbva")
    uso_bbva = obtener_uso_bbva_desde_corte()

    # PLATA se queda igual por ahora
    plata = calcular_tarjeta_plata(
        movs, CONFIG["tarjetas"]["plata"]
    )

    texto = resumen_completo(
        totales,
        saldos,
        sobres,
        edc_bbva,
        uso_bbva,
        plata
    )

    await update.message.reply_text(texto)


async def movimientos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    movs = leer_movimientos()

    if not movs:
        await update.message.reply_text("No hay movimientos registrados.")
        return

    ultimos = movs[-5:]

    mensaje = "🧾 Últimos movimientos:\n"
    for i, m in enumerate(ultimos, start=1):
        mensaje += (
            f"{i}. {m['fecha']} | {m['tipo']} | "
            f"${m['monto']} | {m['categoria']} | {m['cuenta']}\n"
        )

    mensaje += "\nUsa /borrar N para eliminar uno (ej. /borrar 2)"
    await update.message.reply_text(mensaje)

async def borrar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Uso: /borrar N (ej. /borrar 2)")
        return

    try:
        n = int(context.args[0])
        if n < 1 or n > 5:
            raise ValueError
    except ValueError:
        await update.message.reply_text("Debes indicar un número del 1 al 5.")
        return

    movs = leer_movimientos()

    if len(movs) < n:
        await update.message.reply_text("No hay tantos movimientos.")
        return

    indice_real = len(movs) - 5 + (n - 1)
    indice_real = max(indice_real, 0)

    try:
        from storage import borrar_movimiento
        borrar_movimiento(indice_real)
        await update.message.reply_text("🗑️ Movimiento eliminado correctamente.")
    except Exception as e:
        await update.message.reply_text(f"Error al borrar: {e}")

async def plan(update: Update, context: ContextTypes.DEFAULT_TYPE):

    try:
        movs = leer_movimientos()

        sobres = evaluar_sobres_mensuales(
            movs, CONFIG["sobres_mensuales"]
        )

        bbva = construir_estado_bbva()
        efectivo = calcular_efectivo(movs)

        resumen_gastos = resumir_gastos(movs)

        contexto_ia = construir_input_ia(
            sobres=sobres,
            bbva=bbva,
            efectivo=efectivo,
            resumen_gastos=resumen_gastos,
            periodo="2026-01-01 a 2026-01-10"
        )

        prompt = f"""
Eres un asistente financiero personal.

Recibirás un contexto financiero YA CALCULADO.
NO calcules nada.
NO infieras datos.
NO inventes objetivos.

Tu tarea:
- Proponer MÁXIMO 5 acciones concretas.
- Cada acción debe incluir un monto ($), fecha o porcentaje.
- Prioriza riesgos y fechas próximas.
- Si no hay riesgos, dilo explícitamente.

Reglas:
- No sugieras eliminar sobres.
- No propongas acciones imposibles.
- Usa frases cortas y directas.

Contexto:
{contexto_ia}
"""

        respuesta = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Eres un asesor financiero experto."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6
        )

        await update.message.reply_text(
            respuesta.choices[0].message.content
        )

    except Exception as e:
        await update.message.reply_text(
            f"Error al consultar IA: {e}"
        )

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = (
        "📋 *Menú de comandos disponibles*\n\n"
        "💰 *Ingresos y gastos*\n"
        "• `/ingreso monto categoria [cuenta]`\n"
        "  Ej: `/ingreso 4300 trabajo efectivo`\n\n"
        "• `/gasto monto categoria [cuenta]`\n"
        "  Ej: `/gasto 300 gasolina efectivo`\n\n"
        "• `/pago monto categoria [cuenta]`\n"
        "  Ej: `/pago 2000 carro efectivo`\n\n"
        "📊 *Consultas*\n"
        "• `/resumen` – Ver resumen financiero completo\n"
        "• `/movimientos` – Ver los últimos 5 movimientos\n\n"
        "🗑️ *Correcciones*\n"
        "• `/borrar N` – Borrar un movimiento (1–5)\n"
        "  Ej: `/borrar 2`\n\n"
        "🤖 *Inteligencia artificial*\n"
        "• `/plan` – Generar plan financiero con IA\n\n"
        "🆘 *Otros*\n"
        "• `/start` – Activar el bot\n"
        "• `/menu` – Ver este menú\n"
    )

    await update.message.reply_text(texto, parse_mode="Markdown")

async def comando_edc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    texto = update.message.text

    # 1️⃣ Validar tarjeta
    partes = texto.split()
    if len(partes) < 2:
        await update.message.reply_text(
            "Uso correcto:\n/edc bbva"
        )
        return

    tarjeta = partes[1].lower()
    if tarjeta != "bbva":
        await update.message.reply_text(
            "Por ahora solo se soporta BBVA."
        )
        return

    # 2️⃣ Parsear datos del mensaje
    try:
        datos = parsear_edc_texto(texto)
    except ValueError as e:
        await update.message.reply_text(f"❌ Error: {e}")
        return

    # 3️⃣ Completar datos que el usuario NO escribe
    fecha_corte = fecha_ultimo_corte_bbva()
    techo_bbva = 4500

    # 4️⃣ Registrar EDC
    registrar_edc(
        tarjeta="bbva",
        fecha_corte=str(fecha_corte),
        pago_no_intereses=datos["pago_no_intereses"],
        cargos_msi=datos["cargos_msi"],
        pago_minimo=datos["pago_minimo"],
        techo_bbva=techo_bbva
    )

    # 5️⃣ Confirmar al usuario
    await update.message.reply_text(
        f"✅ Estado de cuenta BBVA registrado\n"
        f"📅 Corte: {fecha_corte}\n"
        f"💳 Pago sin intereses: ${datos['pago_no_intereses']:.2f}"
    )

# ▶️ MAIN (UNO SOLO)
def main():
    init_csv()

    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ingreso", ingreso))
    app.add_handler(CommandHandler("gasto", gasto))
    app.add_handler(CommandHandler("pago", pago))
    app.add_handler(CommandHandler("resumen", resumen))
    app.add_handler(CommandHandler("movimientos", movimientos))
    app.add_handler(CommandHandler("borrar", borrar))
    app.add_handler(CommandHandler("plan", plan))
    app.add_handler(CommandHandler("menu", menu))
    app.add_handler(CommandHandler("edc", comando_edc))




    print("🤖 Bot financiero activo...")
    app.run_polling()

if __name__ == "__main__":
    main()
