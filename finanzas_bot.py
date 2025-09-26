import csv
import os
from datetime import datetime
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import json

TOKEN = "8383987370:AAE8OiZUWdTPflNqFktBHAYXBOySPFyRVz4"
CSV_FILE = "movimientos.csv"

MAPA_SOBRES = {
    "ahorro": "ahorro_personal",
    "ahorro_personal": "ahorro_personal",
    "mama": "mama",
    "mamá": "mama",
    "pension": "pension",
    "carro": "carro",
    "gasolina": "gasolina",
    "efectivo": "efectivo"
}

NOMBRES_AMIGABLES = {
    "ahorro_personal": "Ahorro Personal",
    "mama": "Mamá",
    "carro": "Carro",
    "pension": "Pensión",
    "efectivo": "Efectivo",
    "gasolina": "Gasolina",
    "azteca": "banco_azteca",
    "bancoppel": "banco_bancoppel"
}

MAPA_CUENTAS = {
    "azteca": "banco_azteca",
    "banco_azteca": "banco_azteca",
    "bancoppel": "banco_bancoppel",
    "banco_bancoppel": "banco_bancoppel"
}



def init_csv():
    if not os.path.exists(CSV_FILE):
        with open(CSV_FILE, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['fecha', 'tipo', 'monto', 'categoria', 'cuenta'])


def guardar_movimiento(tipo, monto, categoria, cuenta):
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Normaliza el nombre de la cuenta y categoría
    categoria = MAPA_SOBRES.get(categoria, categoria)
    cuenta = MAPA_SOBRES.get(cuenta, cuenta)

    with open(CSV_FILE, mode='a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([fecha, tipo, monto, categoria, cuenta])

def parse_monto(text):
    try:
        return float(text)
    except ValueError:
        return None
    

def generar_resumen_diario():
    hoy = datetime.now().date()
    total_gastos = 0.0
    total_ingresos = 0.0

    sobres_interes = ['gasolina', 'pension', 'carro', 'mama', 'ahorro_personal']
    saldos_sobres = {sobre: 0.0 for sobre in sobres_interes}
    saldo_general_cuentas = {}

    if not os.path.exists(CSV_FILE):
        return "No hay movimientos registrados aún."

    with open(CSV_FILE, mode='r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            fecha = datetime.strptime(row['fecha'], "%Y-%m-%d %H:%M:%S").date()
            monto = float(row['monto'])
            tipo = row['tipo']
            categoria = row['categoria'].lower()
            cuenta = row['cuenta'].lower()

            # Normaliza el nombre del sobre o cuenta usando MAPA_SOBRES o MAPA_CUENTAS
            cuenta = MAPA_SOBRES.get(cuenta, cuenta)  # Primero mira en sobres
            cuenta = MAPA_CUENTAS.get(cuenta, cuenta)  # Luego mira en cuentas

            # Para resumen diario:
            if fecha == hoy:
                if tipo in ['gasto', 'pago']:
                    total_gastos += monto
                elif tipo == 'ingreso':
                    total_ingresos += monto

            # Para calcular saldo por sobre (acumulativo sin importar fecha)
            if cuenta in sobres_interes:
                if tipo == 'ingreso':
                    saldos_sobres[cuenta] += monto
                elif tipo in ['gasto', 'pago']:
                    saldos_sobres[cuenta] -= monto

            # Saldo general por cuenta (efectivo, banco, etc)
            if cuenta not in saldo_general_cuentas:
                saldo_general_cuentas[cuenta] = 0.0

            if tipo == 'ingreso':
                saldo_general_cuentas[cuenta] += monto
            elif tipo in ['gasto', 'pago']:
                saldo_general_cuentas[cuenta] -= monto

    mensaje = (
        f"📅 Resumen financiero de hoy ({hoy}):\n"
        f"💸 Gastos totales: ${total_gastos:.2f}\n"
        f"💰 Ingresos totales: ${total_ingresos:.2f}\n"
        f"🔢 Balance: ${total_ingresos - total_gastos:.2f}\n\n"
        "📦 Saldos actuales en sobres:\n"
    )

    for sobre, saldo in saldos_sobres.items():
        nombre_mostrar = NOMBRES_AMIGABLES.get(sobre, sobre.title().replace("_", " "))
        mensaje += f"- {nombre_mostrar}: ${saldo:.2f}\n"

    mensaje += "\n🏦 Saldo general por cuentas:\n"
    for cuenta, saldo in saldo_general_cuentas.items():
        nombre_mostrar = NOMBRES_AMIGABLES.get(cuenta, cuenta.title().replace("_", " "))
        mensaje += f"- {nombre_mostrar}: ${saldo:.2f}\n"

    return mensaje



# --- Handlers (responden a comandos) ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hola! Estoy activo y listo para ayudarte.")

async def gasto(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Uso: /gasto monto categoria [cuenta]")
        return
    monto = parse_monto(context.args[0])
    if monto is None:
        await update.message.reply_text("Monto inválido.")
        return
    
    categoria = context.args[1].lower()
    cuenta = context.args[2].lower() if len(context.args) >= 3 else "efectivo"
    
    guardar_movimiento("gasto", monto, categoria, cuenta)
    await update.message.reply_text(f"Gasto registrado: ${monto} en {categoria} ({cuenta})")

async def ingreso(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Uso: /ingreso monto categoria [cuenta]")
        return
    monto = parse_monto(context.args[0])
    if monto is None:
        await update.message.reply_text("Monto inválido.")
        return
    categoria = context.args[1].lower()
    cuenta = context.args[2].lower() if len(context.args) >= 3 else "efectivo"
    guardar_movimiento("ingreso", monto, categoria, cuenta)
    await update.message.reply_text(f"Ingreso registrado: ${monto} en {categoria} ({cuenta})")

async def pago(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Uso: /pago monto cuenta")
        return
    monto = parse_monto(context.args[0])
    if monto is None:
        await update.message.reply_text("Monto inválido.")
        return
    cuenta = context.args[1].lower()
    guardar_movimiento("pago", monto, "pago_tarjeta", cuenta)
    await update.message.reply_text(f"Pago registrado: ${monto} a {cuenta}")


async def resumen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = generar_resumen_diario()
    await update.message.reply_text(mensaje)

# === Análisis inteligente ===

def cargar_config():
    with open("config.json", "r") as f:
        return json.load(f)

def calcular_saldos_actuales():
    """
    Lee los movimientos y suma el saldo actual de cada sobre/cuenta.
    Retorna un dict: { "carro": saldo, "pension": saldo, ... }
    """
    saldos = {}
    if not os.path.exists(CSV_FILE):
        return saldos

    with open(CSV_FILE, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cuenta = row['cuenta'].lower()
            monto = float(row['monto'])
            tipo = row['tipo']
            # Inicializa saldo si no existe
            if cuenta not in saldos:
                saldos[cuenta] = 0.0

            if tipo == 'ingreso':
                saldos[cuenta] += monto
            elif tipo in ['gasto', 'pago']:
                saldos[cuenta] -= monto
    return saldos



def generar_consejos_financieros():
    config = cargar_config()
    hoy = datetime.now()
    consejos = []

    saldos = calcular_saldos_actuales()
    sobres = config.get("sobres", {})
    tarjetas = config.get("tarjetas", {})
    
    # Checar prioridades y metas
    for sobre, datos in sobres.items():
        saldo_actual = saldos.get(sobre, 0.0)
        meta = datos.get("meta", 0)
        prioridad = datos.get("prioridad", 99)
        deuda = datos.get("deuda", False)

        # Si hay deuda (ej. mamá)
        if deuda and saldo_actual < meta:
            faltante = meta - saldo_actual
            consejos.append(f"🔴 Aún debes ${faltante:.2f} a {sobre}. Prioriza abonar a esta deuda.")

        # Si no hay deuda, chequea si el saldo es suficiente para meta
        elif saldo_actual < meta:
            faltante = meta - saldo_actual
            consejos.append(f"📌 Te faltan ${faltante:.2f} para cubrir la meta de {sobre}. Considera abonar esa cantidad.")

        else:
            consejos.append(f"✅ {sobre.title()} está cubierto con ${saldo_actual:.2f}.")

    # Revisión de tarjeta platacard y deuda actual
    if "platacard" in tarjetas:
        deuda_actual = tarjetas["platacard"].get("deuda_actual", 0)

        cuentas_posibles = ["efectivo", "azteca", "bancoppel", "platacard"]
        saldo_disponible_para_tarjeta = sum(saldos.get(cuenta, 0) for cuenta in cuentas_posibles)

        if deuda_actual > 0:
            if saldo_disponible_para_tarjeta >= deuda_actual:
                consejos.append(f"💳 Puedes pagar la deuda completa de Platacard (${deuda_actual:.2f}) con el saldo actual.")
            elif saldo_disponible_para_tarjeta > 0:
                faltante = deuda_actual - saldo_disponible_para_tarjeta
                consejos.append(f"⚠️ Solo tienes ${saldo_disponible_para_tarjeta:.2f} para abonar a Platacard. Aún debes ${faltante:.2f}.")
            else:
                consejos.append(f"⚠️ No tienes saldo disponible para abonar a la deuda de Platacard (${deuda_actual:.2f}).")

    # Opcional: muestra saldo libre en efectivo
    saldo_efectivo = saldos.get("efectivo", 0)
    if saldo_efectivo > 0:
        consejos.append(f"💵 Tienes ${saldo_efectivo:.2f} libre en efectivo para gastos o ahorro adicional.")

    if not consejos:
        return "✅ Todo en orden por ahora. Buen manejo financiero."

    return "🧠 Consejos financieros de hoy:\n\n" + "\n".join(consejos)



async def consejo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = generar_consejos_financieros()
    await update.message.reply_text(mensaje)


async def listar_movimientos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not os.path.exists(CSV_FILE):
        await update.message.reply_text("No hay movimientos registrados.")
        return

    with open(CSV_FILE, mode='r') as f:
        reader = list(csv.DictReader(f))
        print("DEBUG: Movimientos leídos:", reader)  # imprime los datos leídos
        ultimos = reader[-5:]
        print("DEBUG: Últimos movimientos:", ultimos)
        if not ultimos:
            await update.message.reply_text("No hay movimientos recientes.")
            return

        mensaje = "🧾 Últimos movimientos:\n"
        for i, row in enumerate(ultimos, start=1):
            mensaje += (
                f"{i}. {row.get('fecha', '')} - {row.get('tipo', '')} - ${row.get('monto', '')} - "
                f"{row.get('categoria', '')} - {row.get('cuenta', '')}\n"
            )
        mensaje += "\nUsa /borrar [número] para eliminar alguno."
        await update.message.reply_text(mensaje)



async def borrar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Uso: /borrar número_del_movimiento (ej. /borrar 2)")
        return

    try:
        index = int(context.args[0]) - 1  # convertir a índice 0-based
    except ValueError:
        await update.message.reply_text("Debes escribir un número válido.")
        return

    if not os.path.exists(CSV_FILE):
        await update.message.reply_text("No hay movimientos registrados.")
        return

    # Leemos el archivo CSV completo
    with open(CSV_FILE, mode='r', newline='') as f:
        reader = list(csv.reader(f))
        encabezado = reader[0]
        datos = reader[1:]

    ultimos = datos[-5:]  # últimos 5 movimientos

    if index < 0 or index >= len(ultimos):
        await update.message.reply_text(f"Número fuera de rango. Solo puedes borrar entre los últimos {len(ultimos)} movimientos.")
        return

    # Calcula el índice real en la lista completa de datos
    indice_real = len(datos) - len(ultimos) + index

    # Elimina el movimiento seleccionado
    del datos[indice_real]

    # Reescribe el archivo CSV con los datos actualizados
    with open(CSV_FILE, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(encabezado)
        writer.writerows(datos)

    await update.message.reply_text("✅ Movimiento eliminado correctamente.")



async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mensaje = (
        "📋 *Menú de comandos disponibles:*\n\n"
        "💰 *Ingresos y Gastos:*\n"
        "• `/ingreso monto categoria [cuenta]` – Registrar un ingreso\n"
        "   Ej: `/ingreso 500 salario efectivo`\n"
        "• `/gasto monto categoria [cuenta]` – Registrar un gasto\n"
        "   Ej: `/gasto 120 gasolina carro`\n"
        "• `/pago monto cuenta` – Registrar pago de tarjeta u otro gasto especial\n"
        "   Ej: `/pago 300 platacard`\n\n"
        "📊 *Resumen y seguimiento:*\n"
        "• `/resumen` – Ver resumen diario de ingresos, gastos y saldos\n"
        "• `/consejo` – Recomendaciones financieras inteligentes\n"
        "• `/movimientos` – Ver los últimos 5 movimientos\n"
        "• `/borrar [número]` – Eliminar un movimiento reciente\n"
        "   Ej: `/borrar 2`\n\n"
        "📦 *Cuentas y sobres reconocidos:*\n"
        "`carro`, `pension`, `mama`, `ahorro`, `efectivo`, `bancoppel`, `azteca`, etc.\n"
        "_(Alias como 'ahorro' → 'ahorro_personal' están mapeados)_\n\n"
        "🆘 *Otros:*\n"
        "• `/start` – Activar el bot\n"
        "• `/menu` – Mostrar este menú de ayuda\n"
    )
    await update.message.reply_text(mensaje, parse_mode="HTML")

# --- MAIN ---

def main():
    init_csv()
    app = ApplicationBuilder().token(TOKEN).build()

    # Registrar comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("gasto", gasto))
    app.add_handler(CommandHandler("ingreso", ingreso))
    app.add_handler(CommandHandler("pago", pago))
    app.add_handler(CommandHandler("resumen", resumen))
    app.add_handler(CommandHandler("consejo", consejo))
    app.add_handler(CommandHandler("movimientos", listar_movimientos))
    app.add_handler(CommandHandler("borrar", borrar))
    app.add_handler(CommandHandler("menu", menu))


    print("Bot iniciado...")
    app.run_polling()


if __name__ == '__main__':
    main()
