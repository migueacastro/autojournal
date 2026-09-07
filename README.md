# AutoJournal 📝

AutoJournal is a Python application that automatically generates a changelog or activity report from the git logs of your local repositories. It can extract raw logs or use the Gemini API to create intelligent, readable summaries exported to Markdown or PDF.

## Features

- **Automated Changelog Generation:** Creates a clean, formatted changelog from your git commits.
- **Dual Output Formats:** Export your reports as standard Markdown (`.md`) or professional PDF (`.pdf`) documents.
- **AI-Powered Summaries (Optional):** Use Google's Gemini API to translate and summarize technical commits into a clean executive report.
- **Multi-Repository Support:** Scans multiple local git repositories at once.
- **Multi-Branch Support:** Scan one or several branches per repository, separated by `|` (e.g., `main|develop`).
- **Customizable Timeframe:** Specify the timeframe for the git logs (e.g., "1 day ago", "2 weeks ago"). Relative dates are resolved to real dates for the report header and filename.
- **Smart File Naming:** Reports are saved as `Reporte <USER_FULLNAME> del <desde> al <hasta>.<ext>`, e.g. `Reporte Miguel Castro del 24-08-2026 al 07-09-2026.pdf`.

## Prerequisites

Before you begin, ensure you have the following installed:

- [Python 3.6+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)

## Installation & Setup

1.  **Clone the repository:**

    ```bash
    git clone [https://github.com/migueacastro/autojournal](https://github.com/migueacastro/autojournal)
    cd autojournal
    ```

2.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3.  **Create and configure the `.env` file:**
    Create a file named `.env` in the root of the project with the following content:

    ```env
    # Your Google Gemini API Key (Required only if using the -ai flag)
    GEMINI_API_KEY="YOUR_API_KEY"

    # List of absolute paths to your local git repositories (JSON format)
    PATH_LIST='["/path/to/repo1", "/path/to/repo2"]'

    # Your Git email (used to filter commits; also the fallback for the report title)
    EMAIL_GIT="your-email@example.com"

    # Your full name (used for the report header and the output filename)
    USER_FULLNAME="Your Name"

    # (Optional) Branch/branches to scan. Use "|" to scan several branches, e.g. "main|develop|release".
    # Branches that don't exist in a repository are skipped automatically.
    BRANCH_NAME="main"

    # The timeframe for the git logs. Accepts relative dates ("2 weeks ago", "today",
    # "yesterday", "last month") or absolute ones ("2026-08-05", "05/08/2026").
    SINCE_DATE="2 weeks ago"
    UNTIL_DATE="today"

    # (Optional) The absolute folder where the report will be saved. Only the folder
    # changes — the filename is always generated automatically
    # ("Reporte <name> del <desde> al <hasta>").
    SAVE_PATH="/path/to/save/folder"

    # (Optional) A custom prompt for the Gemini API
    PROMPT_TEMPLATE="Your custom prompt here"
    ```

    **Note:** You can get your Gemini API key from [Google AI Studio](https://aistudio.google.com/app/apikey).

## Usage

To run the application, execute the `main.py` script from the root of the project:

```bash
python src/main.py
```

### Options

- `-h, --help`: Show Help Message.
- `-lk, --loadkey`: Load and save Gemini API Key to `.env`.
- `-s, --since`: Specify Since Date (e.g., "2023-01-01" or "yesterday").
- `-u, --until`: Specify Until Date.
- `-ai, --use-ai`: Uses Gemini to create a summary based on logs. If skipped, it generates a raw list of commits.
- `-f, --format`: Output format for the report. Choices: `md` (Markdown) or `pdf` (PDF). (Default: `pdf`).

The script will:

1.  Read configuration from `.env`.
2.  Fetch git logs from specified repositories filtering by `EMAIL_GIT` and `BRANCH_NAME` (one or more branches separated by `|`).
3.  Generate content (AI summary or raw logs).
4.  Add a header with the real period covered (relative dates like "2 weeks ago" are resolved to actual dates).
5.  Save the report to `SAVE_PATH` or, by default, to `outputs/Reporte <USER_FULLNAME> del <desde> al <hasta>.<ext>` (e.g. `outputs/Reporte Your Name del 24-08-2026 al 07-09-2026.pdf`).

## Customization

You can customize the following in your `.env` file:

- **`PROMPT_TEMPLATE`**: Alter the style, language, or structure of the AI-generated report.
- **`SAVE_PATH`**: Specify a different absolute folder for the output files. It only changes the destination folder; the filename is always generated automatically as `Reporte <name> del <desde> al <hasta>`.
- **`EMAIL_GIT`**: Ensure this matches your git configuration (`git config user.email`) to correctly filter your activity.
- **`BRANCH_NAME`**: If set, the script will only look for commits in those branches across all repositories. Separate multiple branches with `|` (e.g., `BRANCH_NAME=main|develop|mirama3`). Branches missing from a repository are skipped with a warning instead of failing the run.
- **`USER_FULLNAME`**: Sets the name displayed in the report header and used in the output filename.
- **`SINCE_DATE` / `UNTIL_DATE`**: Accept relative ("2 weeks ago", "today") or absolute ("2026-08-05", "05/08/2026") dates. They are normalized to ISO (YYYY-MM-DD) before being passed to Git — so any format works correctly — and resolved to real dates for the header and the filename.

---
