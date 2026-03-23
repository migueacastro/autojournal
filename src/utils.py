import os
import subprocess
import json
from datetime import datetime
import markdown
from xhtml2pdf import pisa
from google import genai
from google.genai import types
from dotenv import load_dotenv, set_key, get_key

# Construct the path to the .env file in the parent directory
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))

load_dotenv(dotenv_path=dotenv_path)

USERNAME_GIT = (
    get_key(dotenv_path, "USERNAME_GIT")
    if get_key(dotenv_path, "USERNAME_GIT")
    else "user"
)
USER_FULLNAME = (get_key(dotenv_path, "USER_FULLNAME")
    if get_key(dotenv_path, "USER_FULLNAME")
    else ""
)
CURRENT_DATE = datetime.now().strftime("%Y-%m-%d")
DEFAULT_FILE_NAME = f"cambios-{USERNAME_GIT}-{CURRENT_DATE}.md"
DEFAULT_SAVE_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "outputs", DEFAULT_FILE_NAME)
)
DEFAULT_SINCE_DATE = "2 weeks ago"
DEFAULT_UNTIL_DATE = "today"

SAVE_PATH = (
    get_key(dotenv_path, "SAVE_PATH")
    if get_key(dotenv_path, "SAVE_PATH")
    else DEFAULT_SAVE_PATH
)
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
BRANCH_NAME = get_key(dotenv_path, "BRANCH_NAME")


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
            git_cmd.append(BRANCH_NAME)
            
        git_cmd.extend([
            f"--author={USERNAME_GIT}", 
            "--since", SINCE_DATE, 
            "--until", UNTIL_DATE, 
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


def format_raw_markdown(logs: str) -> str:
    """
        Genera la estructura del documento cuando no se usa Gemini.
    """
    header = f"#Reporte de Cambios ({SINCE_DATE} a {UNTIL_DATE})\n\n"
    #header += "> *Nota: Reporte generado automáticamente desde le historial de Git"
    return header + logs


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


def save_output_to_markdown(content: str, path: str = SAVE_PATH):
    """
    Guardar la salida a un archivo markdown en una ruta
    """
    try:
        output_dir = os.path.dirname(path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        # If path already exists, save it with a counter name ie: file_1,file_2 etc
        final_path = path
        if os.path.exists(final_path):

            base, extension = os.path.splitext(path)
            counter = 1

            # Buscamos un nombre que no esté ocupado
            while os.path.exists(f"{base}_{counter}{extension}"):
                counter += 1

            path = f"{base}_{counter}{extension}"

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Contenido guardado exitosamente en: {path}")
    except IOError as e:
        print(f"Error al guardar el archivbo en {path}: {e}")


def set_gemini_key(key: str) -> None:
    set_key(dotenv_path, "GEMINI_API_KEY", key)


def set_since_date(date: str) -> str:
    set_key(dotenv_path, "SINCE_DATE", date)
    return date


def set_until_date(date:str) -> str:
    set_key(dotenv_path, "UNTIL_DATE", date)
    return date


def save_output_to_pdf(content: str, path: str = SAVE_PATH):
    """
    Convertir el contenido Markdown a HTML y guardarlo como PDF usando xhtml2pdf.
    """
    try:
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