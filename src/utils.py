import os
import subprocess
import json
from datetime import datetime
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

DEFAULT_PROMPT_TEMPLATE = """
Eres un auditor de código IA. Tu tarea es revisar los commits que realizo el usuario en los proporcionados y hacer una lista por fecha de los cambios y la actividad del usuario. Debes plasmarlo como un changelog en un texto de tipo Markdown con todo los cambios en español y en orden descendente (desde recientes a mas antiguos). exceptuando nombres propios claro y no digas ningun preambulo con "aqui tienes un changelog". Solo muestra el changelog. de la siguiente manera:
  # (Fecha: DD/MM/AAAA)
    ## Repositorio: (Nombre del repositorio)
     - Descripción del cambio 1 en el repositorio x
     - Descripcion del cambio 2 en el repositorio x
     - Descripción del cambio 1 en el repositorio y
     - Descripcion del cambio 2 en el repositorio y
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
    client = genai.Client(api_key=GEMINI_API_KEY)
    print()
    return client


def execute_git_log(path):
    """
    Ejecutar git log en una ruta
    """
    if not os.path.isdir(path):
        return

    repo_name = os.path.basename(os.path.abspath(path))

    try:

        log_output = subprocess.check_output(
            ["git", "log", f'--since="{SINCE_DATE}"', f'--until="{UNTIL_DATE}"'],
            cwd=path,
            text=True,
            stderr=subprocess.STDOUT,
            encoding="utf-8",
        )
        return f"--- Repositorio: {repo_name} ---\n{log_output}"

    except FileNotFoundError:
        print(
            "Error: El comando 'git' no se encontró. Asegúrate de que Git esté instalado y su ejecutable en el PATH del sistema."
        )
        return ""

    except subprocess.CalledProcessError as e:

        error_message = e.output
        if "not a git repository" in error_message.lower():
            print(f"{path} no es un repositorio de git.\n")

        return ""


def execute_git_log_in_paths(paths):
    """
    Ejecutar git log en varias rutas
    """
    all_logs = []
    for path in paths:
        all_logs.append(execute_git_log(path))

    return "\\n".join(all_logs)  # Unir logs con \n


def prompt_with_logs(client: genai.Client, text: str):
    """
    Pasar los logs a un prompt de GEMINI
    """
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
    return response.text


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


def set_since_date(date: str) -> None:
    set_key(dotenv_path, "SINCE_DATE", date)


def set_until_date(date:str) -> None:
    set_key(dotenv_path, "UNTIL_DATE", date)
