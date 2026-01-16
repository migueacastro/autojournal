import utils as u
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
        u.set_gemini_key(args.loadkey)
        print("Gemini API Key has been set")
        return

    if args.since:
        u.SINCE_DATE = u.set_since_date(args.since)

    if args.until:
        u.UNTIL_DATE = u.set_until_date(args.until)

    client = u.create_client()
    paths = u.PATH_LIST

    print(f"Getting logs since {u.SINCE_DATE} until {u.UNTIL_DATE}")
    all_logs = u.execute_git_log_in_paths(paths)

    result = u.prompt_with_logs(client, all_logs)

    u.save_output_to_markdown(result)


if __name__ == "__main__":
    main()
