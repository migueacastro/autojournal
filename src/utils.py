import os
from dotenv import load_dotenv, set_key, get_key
from google import genai
import json
from datetime import datetime
import subprocess

# Construct the path to the .env file in the parent directory
dotenv_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))

load_dotenv(dotenv_path=dotenv_path)

USERNAME_GIT = get_key(dotenv_path, "USERNAME_GIT") if get_key(dotenv_path, "USERNAME_GIT") else "user"
CURRENT_DATE = datetime.now().strftime("%Y-%m-%d")
DEFAULT_FILE_NAME = f"cambios-{USERNAME_GIT}-{CURRENT_DATE}.md"
DEFAULT_SAVE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "outputs",DEFAULT_FILE_NAME))
SAVE_PATH = get_key(dotenv_path, "SAVE_PATH") if get_key(dotenv_path, "SAVE_PATH") else DEFAULT_SAVE_PATH

DEFAULT_PROMPT_TEMPLATE = """
Eres un auditor de código IA. Tu tarea es revisar los commits que realizo el usuario en los proporcionados y hacer una lista por fecha de los cambios y la actividad del usuario. Debes plasmarlo en un texto de tipo Markdown de la siguiente manera:
  # (Fecha: DD/MM/AAAA)
    ## Repositorio: (Nombre del repositorio)
     - Descripción del cambio 1 en el repositorio x
     - Descripción del cambio 2 en el repositorio y"""

GEMINI_API_KEY = get_key(dotenv_path, "GEMINI_API_KEY")
PATH_LIST = json.loads(get_key(dotenv_path, "PATH_LIST")) if get_key(dotenv_path, "PATH_LIST") else []
PROMPT_TEMPLATE = get_key(dotenv_path, "PROMPT_TEMPLATE") if get_key(dotenv_path, "PROMPT_TEMPLATE") else DEFAULT_PROMPT_TEMPLATE



def prompt_api_key() -> None:
    global GEMINI_API_KEY

    # Check .env api key
    if GEMINI_API_KEY:
        try:
            genai.configure(api_key=GEMINI_API_KEY)
            list(genai.list_models())
            print("Existing GEMINI API KEY is valid.")
            return

        except Exception as e:
            print("Existing GEMINI API KEY is invalid.")
            GEMINI_API_KEY = None

    # If no valid key, enter the loop to prompt for one.
    while True:
        key = str(input("Please paste your GEMINI API KEY here\n: ")).strip()
        if not key:
            continue
        try:
            genai.configure(api_key=key)
            list(genai.list_models())  # Test call

            # If we are here, the key is valid.
            os.environ["GEMINI_API_KEY"] = key
            set_key(dotenv_path, "GEMINI_API_KEY", key)
            print("GEMINI API KEY has been validated and saved.")
            GEMINI_API_KEY = key
            break  # Exit loop

        except Exception as e:
            print("Invalid API Key. Please try again.")

def prompt_path_list() -> None:
    global PATH_LIST


    if len(PATH_LIST) > 0:
        #validate each path
        pass

    while True:
        path = str(input("Please paste the project path here (Cancel with empty input)\n: ")).strip()
        if not path:
            if len(PATH_LIST) > 0:
                break
            else:
                print("No paths entered. Please try again")
                continue
        PATH_LIST.append(path)
    return PATH_LIST



    



def start_gemini():
    global GEMINI_API_KEY
    # By the time this is called, prompt_api_key should have ensured a valid key.
    # The genai module is already configured by prompt_api_key.
    client = genai.Client()  # Client will use the globally configured key
    return client


def execute_git_command_in_paths(paths, command_args) -> str: 
    """
    Executes a given command in each of the provided git repository paths.

    Args:
        paths (list): A list of paths to Git repositories.
        command_args (list): The command to execute as a list of strings
                             (e.g., ['git', 'log', '--oneline', '-n', '5']).
    """
    GIT_LOG_TEXT = ""

    for repo_path in paths:
        # Check if it's a git repository
        if not os.path.isdir(os.path.join(repo_path, ".git")):
            print(f"--- Skipping {repo_path}: Not a Git repository. ---")
            continue

        print(f"--- Executing in: {repo_path} ---")
        try:
            # Execute the command in the repository's directory
            result = subprocess.run(
                command_args,
                cwd=repo_path,  # Run command in this directory
                capture_output=True,  # Capture stdout and stderr
                text=True,  # Decode output as text
                check=True,  # Raise an exception on non-zero exit codes
            )
            GIT_LOG_TEXT += f"\n--- Output from {repo_path} ---\n"
            GIT_LOG_TEXT += result.stdout
            print(result.stdout)

        except FileNotFoundError:
            print(
                f"Error: Command '{command_args[0]}' not found. Is Git installed and in your PATH?"
            )
            return  # Stop further execution
        except subprocess.CalledProcessError as e:
            print(f"Error executing command in {repo_path}:")
            print(e.stderr)
    return GIT_LOG_TEXT


def execute_gemini_prompt(client, prompt: str) -> str:
    """
    Executes a Gemini API prompt and returns the response text.

    Args:
        client: The Gemini API client.
        prompt (str): The prompt text to send to the Gemini API.

    Returns:
        str: The response text from the Gemini API.
    """
    response = client.chat.completions.create(
        model="gemini-1.5-pro",
        messages=[
            {"role": "user", "content": prompt}
        ],
        max_output_tokens=1024,
    )
    return response.choices[0].message.content


def save_response_to_file(response_text: str, filename: str) -> None:
    """
    Saves the given response text to a file.

    Args:
        response_text (str): The text to save.
        filename (str): The name of the file to save the text to.
    """
    with open(filename, "w") as file:
        file.write(response_text)
    print(f"Response saved to {filename}")

