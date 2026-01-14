from utils import *
import argparse


def main():

    parser = argparse.ArgumentParser(
        prog="autojournal",
        description="Make a changelog automatically using Gemini and Git Log in each of the repos in your .env file",
        epilog="Use autojournal --help to show list of commands",
    )

    parser.add_argument(
        "-lk", "--loadkey", type=str, help="Load Gemini API Key", metavar="LOADKEY"
    )

    parser.add_argument(
        "-s",
        "--since",
        type=str,
        help="Since date in DD/MM/YYYY or 'today' or '2 weeks ago'",
        metavar="SINCE",
    )

    parser.add_argument(
        "-u",
        "--until",
        type=str,
        help="Until date in DD/MM/YYYY or 'today' or '2 weeks ago'",
        metavar="UNTIL",
    )

    args = parser.parse_args()

    if args.loadkey:
        set_gemini_key(args.loadkey)
        print("Gemini API Key has been set")
        return

    if args.since:
        set_since_date(args.since)

    if args.until:
        set_until_date(args.until)

    client = create_client()
    paths = PATH_LIST

    print(f"Getting logs since {SINCE_DATE} until {UNTIL_DATE}")
    all_logs = execute_git_log_in_paths(paths)

    result = prompt_with_logs(client, all_logs)

    save_output_to_markdown(result)


if __name__ == "__main__":
    main()
