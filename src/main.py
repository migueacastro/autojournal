from utils import *




client = create_client()
paths = PATH_LIST

all_logs = execute_git_log_in_paths(paths)

result = prompt_with_logs(client, all_logs)

save_output_to_markdown(result)




