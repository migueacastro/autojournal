
from utils import *










def main():
  prompt_api_key()
  paths = prompt_path_list()  
  client = start_gemini()
  execute_git_command_in_paths(paths, ['git', 'log', '--oneline', '-n', '5'])

  

if __name__ == "__main__":
  main()