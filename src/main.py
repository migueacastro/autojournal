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

    parser.add_argument(
        "-ai",
        "--use-ai",
        action="store_true",
        help="Uses gemini to make a brief based on logs. If skipped, it will generate a list with the logs instead."
    )

    parser.add_argument(
        "-f",
        "--format",
        type=str,
        choices=["md", "pdf"],
        default="pdf",
        help="Formato de salida del reporte: 'md' para Markdown o 'pdf' para PDF. Por defecto es 'pdf'."
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
    
    client = None
    result = None
    paths = u.PATH_LIST

    print(f"Getting logs since {u.SINCE_DATE} until {u.UNTIL_DATE}")
    all_logs = u.execute_git_log_in_paths(paths)

    if not all_logs.strip():
        print("No commits were found in the repositories between these dates.")
        return

    if args.use_ai:
        print("Generating content with Gemini...")
        client = u.create_client()
        result = u.prompt_with_logs(client, all_logs)
    else:
        print("Generating logs with logs...")
        result = u.format_raw_markdown(all_logs)

    

    #u.save_output_to_markdown(result)
    if args.format == "pdf":
        print("Exportando reporte a formato PDF...")
        u.save_output_to_pdf(result)
    else:
        print("Guardando reporte en formato Markdown...")
        u.save_output_to_markdown(result)


if __name__ == "__main__":
    main()
