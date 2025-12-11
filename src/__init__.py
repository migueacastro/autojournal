
from utils import *










def main(*args, **kwargs):
  prompt_api_key()
  paths = prompt_path_list()  
  client = start_gemini()
  text = execute_git_command_in_paths(paths, ['git', 'log', '--oneline', '-n', '5'])
  result = execute_gemini_prompt(client, text)
  save_response_to_file(result, SAVE_PATH)

  

if __name__ == "__main__":
  main()