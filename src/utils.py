import os
import re
import subprocess
import json
from calendar import monthrange
from datetime import datetime, timedelta
import markdown
from xhtml2pdf import pisa
from google import genai
from google.genai import types
from dotenv import load_dotenv, set_key, get_key

# Construct the path to the .env file in the parent directory
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))

load_dotenv(dotenv_path=dotenv_path)

EMAIL_GIT = (
    get_key(dotenv_path, "EMAIL_GIT")
    if get_key(dotenv_path, "EMAIL_GIT")
    else "user"
)
USER_FULLNAME = (get_key(dotenv_path, "USER_FULLNAME")
    if get_key(dotenv_path, "USER_FULLNAME")
    else ""
)
# Nombre que aparece en el encabezado y en el nombre del archivo
DISPLAY_NAME = USER_FULLNAME if USER_FULLNAME else EMAIL_GIT

DEFAULT_SINCE_DATE = "2 weeks ago"
DEFAULT_UNTIL_DATE = "today"

SINCE_DATE = (
    get_key(dotenv_path, "SINCE_DATE")
    if get_key(dotenv_path, "SINCE_DATE")
    else DEFAULT_SINCE_DATE
)
UNTIL_DATE = (
    get_key(dotenv_path, "UNTIL_DATE")
    if get_key(dotenv_path, "UNTIL_DATE")
    else DEFAULT_UNTIL_DATE
)

OUTPUT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "outputs"))
SAVE_PATH_ENV = get_key(dotenv_path, "SAVE_PATH")
BRANCH_NAME = get_key(dotenv_path, "BRANCH_NAME")

FILENAME_INVALID_CHARS_RE = re.compile(r'[\\/:*?"<>|]')
RELATIVE_DATE_RE = re.compile(r"^(\d+)\s*(day|week|month|year)s?\s*(?:ago)?$", re.IGNORECASE)


def _subtract_months(dt: datetime, months: int) -> datetime:
    """
    Restar N meses a una fecha sin desbordar el día (ej: 31 de marzo -> 28/29 de febrero).
    """
    total = dt.year * 12 + (dt.month - 1) - months
    year, month_zero_based = divmod(total, 12)
    month = month_zero_based + 1
    day = min(dt.day, monthrange(year, month)[1])
    return dt.replace(year=year, month=month, day=day)


def resolve_date(date_str: str):
    """
    Convierte fechas relativas ('2 weeks ago', 'today', 'yesterday', 'last month')
    o absolutas ('2026-08-05', '05/08/2026', '05-08-2026') en un datetime.
    También acepta el formato de Git con puntos ('2.weeks.ago').
    Devuelve None si no se puede interpretar.
    """
    value = (date_str or "").strip().lower().replace(".", " ")
    now = datetime.now()

    if value in ("today", "hoy", "now"):
        return now
    if value in ("yesterday", "ayer"):
        return now - timedelta(days=1)
    if value in ("last week", "semana pasada"):
        return now - timedelta(weeks=1)
    if value in ("last month", "mes pasado"):
        return _subtract_months(now, 1)

    match = RELATIVE_DATE_RE.match(value)
    if match:
        amount, unit = int(match.group(1)), match.group(2)
        if unit == "day":
            return now - timedelta(days=amount)
        if unit == "week":
            return now - timedelta(weeks=amount)
        if unit == "month":
            return _subtract_months(now, amount)
        if unit == "year":
            return _subtract_months(now, 12 * amount)

    for date_format in ("%Y-%m-%d", "%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(value, date_format)
        except ValueError:
            continue

    return None


def display_date(date_str: str) -> str:
    """
    Fecha resuelta en formato DD/MM/YYYY para mostrar en el reporte.
    Si no se puede resolver, se muestra el texto original.
    """
    resolved = resolve_date(date_str)
    return resolved.strftime("%d/%m/%Y") if resolved else str(date_str)


def filename_date(date_str: str) -> str:
    """
    Fecha resuelta en formato DD-MM-YYYY (sin caracteres inválidos) para el nombre del archivo.
    """
    resolved = resolve_date(date_str)
    raw = resolved.strftime("%d-%m-%Y") if resolved else str(date_str)
    return FILENAME_INVALID_CHARS_RE.sub("-", raw)


def git_since_date(date_str: str) -> str:
    """
    Fecha para el --since de Git, normalizada a ISO (YYYY-MM-DD).
    Git no interpreta bien formatos como DD/MM/YYYY (los lee mes primero),
    así que se la pasamos ya resuelta.
    """
    resolved = resolve_date(date_str)
    return resolved.strftime("%Y-%m-%d") if resolved else str(date_str)


def git_until_date(date_str: str) -> str:
    """
    Fecha para el --until de Git en ISO, al final del día (23:59:59) para
    incluir todos los commits de ese día.
    """
    resolved = resolve_date(date_str)
    if not resolved:
        return str(date_str)
    return f"{resolved.strftime('%Y-%m-%d')} 23:59:59"


def compute_save_path() -> str:
    """
    Ruta de salida del reporte. El nombre del archivo siempre se genera
    automáticamente ('Reporte {nombre} del {desde} al {hasta}'); SAVE_PATH del .env,
    si está definido, solo cambia la carpeta de destino (por defecto: outputs/).
    """
    output_dir = SAVE_PATH_ENV if SAVE_PATH_ENV else OUTPUT_DIR
    safe_name = FILENAME_INVALID_CHARS_RE.sub("-", DISPLAY_NAME).strip()
    file_name = (
        f"Reporte {safe_name} del {filename_date(SINCE_DATE)} al {filename_date(UNTIL_DATE)}"
    )
    return os.path.join(output_dir, file_name)


SAVE_PATH = compute_save_path()


DEFAULT_PROMPT_TEMPLATE = """
Actúa como un Experto Redactor Técnico de Changelogs. Tu tarea es procesar los logs crudos de Git proporcionados y generar un registro de cambios limpio, profesional y legible en español.

TU FUENTE DE VERDAD:
Usa EXCLUSIVAMENTE el texto de los logs proporcionados a continuación. NO inventes repositorios, fechas ni commits que no aparezcan en el texto de entrada. Si un repositorio no tiene actividad en los logs, IGNÓRALO.

REGLAS DE FORMATO (ESTRICTAS):
1. NO uses bloques de código (ni ```markdown ni ```). Devuelve texto plano formateado.
2. NO incluyas introducciones ni conclusiones ("Aquí está tu lista...", "Espero haber ayudado").
3. Orden descendente por fecha (lo más nuevo arriba).
4. Agrupa los cambios primero por FECHA y luego por REPOSITORIO.

ESTRUCTURA DE SALIDA REQUERIDA:
## Fecha: DD/MM/AAAA
### Repositorio: <Nombre Exacto del Repositorio>
- <Descripción clara y concisa del cambio en español>
- <Descripción clara y concisa del cambio en español>

REGLAS DE CONTENIDO:
- Traduce los mensajes técnicos al español, pero mantén términos estándar (como endpoint, frontend, backend, bug, fix).
- Si hay múltiples commits repetitivos (ej: "wip", "fix typo"), resúmelos en una sola línea coherente.
- Elimina mensajes de merge automáticos irrelevantes.
- Traduce los mensajes técnicos al español, pero mantén términos estándar (como endpoint, frontend, backend, bug, fix).
- Reemplaza etiquetas como "WIP" por frases más profesionales como "Fase inicial" o "En progreso".
"""

GEMINI_API_KEY = get_key(dotenv_path, "GEMINI_API_KEY")
PATH_LIST = (
    json.loads(get_key(dotenv_path, "PATH_LIST"))
    if get_key(dotenv_path, "PATH_LIST")
    else []
)
PROMPT_TEMPLATE = (
    get_key(dotenv_path, "PROMPT_TEMPLATE")
    if get_key(dotenv_path, "PROMPT_TEMPLATE")
    else DEFAULT_PROMPT_TEMPLATE
)


def create_client():
    """
    Crear cliente de GEMINI
    """
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY variable not found in environment.")
        print("Use -lk <YOUR_GEMINI_API_KEY> to load the api key first.")
        exit(1)

    client = genai.Client(api_key=GEMINI_API_KEY)
    print()
    return client


def execute_git_log(path):
    """
    Ejecutar git log en una ruta
    """
    
    clean_path = os.path.normpath(path)

    if not os.path.isdir(clean_path):
        return ""
    repo_name = os.path.basename(os.path.abspath(clean_path))
    try:
        git_cmd = ["git", "log"]

        if BRANCH_NAME:
            # BRANCH_NAME admite varias ramas separadas por '|', ej: "main|develop"
            branches = [b.strip() for b in BRANCH_NAME.split("|") if b.strip()]
            valid_branches = []
            for branch in branches:
                check = subprocess.run(
                    ["git", "rev-parse", "--verify", "--quiet", branch],
                    cwd=clean_path,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                if check.returncode == 0:
                    valid_branches.append(branch)
                else:
                    print(f"'{branch}' no existe en {repo_name}, se omite.\n")

            if not valid_branches:
                print(f"Ninguna de las ramas ({BRANCH_NAME}) existe en {repo_name}.\n")
                return ""

            git_cmd.extend(valid_branches)
        git_cmd.extend([
            f"--author={EMAIL_GIT}",
            "--since", git_since_date(SINCE_DATE),
            "--until", git_until_date(UNTIL_DATE),
            "--no-merges",
            "--date=short",
            "--pretty=format:- **%ad**: %s"
        ])
        log_output = subprocess.check_output(
            git_cmd,
            cwd=clean_path,
            text=True,
            stderr=subprocess.STDOUT,
            encoding="utf-8",
        )
        if not log_output.strip():
            return ""
        return f"\n### Repositorio: {repo_name}\n{log_output}\n"

    except FileNotFoundError:
        print(
            "Error: El comando 'git' no se encontró. Asegúrate de que Git esté instalado y su ejecutable en el PATH del sistema."
        )
        return ""

    except subprocess.CalledProcessError as e:

        error_message = e.output
        if "not a git repository" in error_message.lower():
            print(f"{clean_path} no es un repositorio de git.\n")

        return ""


def execute_git_log_in_paths(paths):
    """
    Ejecutar git log en varias rutas
    """
    all_logs = []
    print(paths)
    for path in paths:
        log = execute_git_log(path)
        if log:
            all_logs.append(log)

    return "\n".join(all_logs)  # Unir logs con \n


def prompt_with_logs(client: genai.Client, text: str):
    """
    Pasar los logs a un prompt de GEMINI
    """
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_text(text=PROMPT_TEMPLATE),
                types.Part.from_text(text=text),
            ],
            config=types.GenerateContentConfig(
                temperature=0.1,
            ),
        )

        if response and hasattr(response, "text") and response.text:
            # Limpiar marcas de markdown
            clean_text = (
                response.text.replace("```markdown", "").replace("```", "").strip()
            )
            return clean_text
        else:
            print("La respuesta de la API de Gemini no contiene texto.")
            return ""

    except Exception as e:
        print(f"An unexpected error occurred while calling the Gemini API: {e}")
        return ""


def save_output_to_markdown(content: str, path: str = None):
    """
    Guardar la salida a un archivo markdown en una ruta
    """
    try:
        path = path if path else SAVE_PATH
        base, _ = os.path.splitext(path)
        path = f"{base}.md"

        output_dir = os.path.dirname(path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        # If path already exists, save it with a counter name ie: file_1,file_2 etc
        if os.path.exists(path):

            counter = 1

            # Buscamos un nombre que no esté ocupado
            while os.path.exists(f"{base}_{counter}.md"):
                counter += 1

            path = f"{base}_{counter}.md"

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Contenido guardado exitosamente en: {path}")
    except IOError as e:
        print(f"Error al guardar el archivo en {path}: {e}")


def set_gemini_key(key: str) -> None:
    set_key(dotenv_path, "GEMINI_API_KEY", key)


def set_since_date(date: str) -> str:
    set_key(dotenv_path, "SINCE_DATE", date)
    return date


def set_until_date(date:str) -> str:
    set_key(dotenv_path, "UNTIL_DATE", date)
    return date


def save_output_to_pdf(content: str, path: str = None):
    """
    Convertir el contenido Markdown a HTML y guardarlo como PDF usando xhtml2pdf.
    """
    try:
        path = path if path else SAVE_PATH
        base, _ = os.path.splitext(path)
        pdf_path = f"{base}.pdf"
        
        output_dir = os.path.dirname(pdf_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        if os.path.exists(pdf_path):
            counter = 1
            while os.path.exists(f"{base}_{counter}.pdf"):
                counter += 1
            pdf_path = f"{base}_{counter}.pdf"

        html_content = markdown.markdown(content)
        
        # xhtml2pdf specific CSS fixes
        styled_html = f"""
        <html>
        <head>
            <style>
                @page {{
                    size: a4 portrait;
                    margin: 2cm;
                }}
                body {{ 
                    font-family: Helvetica, Arial, sans-serif; 
                    font-size: 11pt;
                    color: #333; 
                }}
                h2 {{ 
                    color: #34495e; 
                    border-bottom: 1px solid #eee;
                    padding-bottom: 4px;
                    padding-top: 15px; 
                    font-size: 14pt;
                }}
                h3 {{
                    color: #7f8c8d;
                    font-size: 12pt;
                    margin-top: 10px;
                    margin-bottom: 5px;
                }}
                p {{
                    margin-bottom: 10px;
                }}
                li {{ 
                    margin-bottom: 6px; 
                }}
            </style>
        </head>
        <body>
            {html_content}
        </body>
        </html>
        """
        
        # Generar el PDF
        with open(pdf_path, "wb") as pdf_file:
            pisa_status = pisa.CreatePDF(styled_html, dest=pdf_file)

        if pisa_status.err:
            print(f"Hubo un error al generar el PDF: {pisa_status.err}")
        else:
            print(f"PDF Report successfully generated at: {pdf_path}")
        
    except Exception as e:
        print(f"Error while generating PDF: {e}")