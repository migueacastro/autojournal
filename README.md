# AutoJournal 📝

AutoJournal is a Python application that automatically generates a changelog or activity report from the git logs of your local repositories using the Gemini API.

## Features

- **Automated Changelog Generation:** Creates a clean, markdown-formatted changelog from your git commits.
- **Multi-Repository Support:** Scans multiple local git repositories.
- **Customizable Timeframe:** Specify the timeframe for the git logs (e.g., "1 day ago", "2 weeks ago").
- **Customizable Output:** Tailor the output file name and save path.
- **Powered by Gemini:** Uses Google's Gemini API for intelligent log summarization.

## Prerequisites

Before you begin, ensure you have the following installed:

- [Python 3.6+](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)

## Installation & Setup

1.  **Clone the repository:**

    ```bash
    git clone https://github.com/migueacastro/autojournal
    cd autojournal
    ```

2.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3.  **Create and configure the `.env` file:**
    Create a file named `.env` in the root of the project with the following content:

    ```env
    # Your Google Gemini API Key
    GEMINI_API_KEY="YOUR_API_KEY"

    # List of absolute paths to your local git repositories (JSON format)
    PATH_LIST='["/path/to/repo1", "/path/to/repo2"]'

    # Your Git username (used for the output file name)
    USERNAME_GIT="your-username"

    # The timeframe for the git logs (e.g., "1 day ago", "2 weeks ago", "2024-01-01")
    SINCE_DATE="2 weeks ago"

    # (Optional) The absolute path to save the output file
    SAVE_PATH="/path/to/save/output.md"

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

- -h, --help : Show Help Message
- -lk, --loadkey : Load Gemini API Key
- -s, --since : Specify Since Date

The script will then:

1.  Read the configuration from your `.env` file.
2.  Fetch the git logs from the specified repositories.
3.  Generate a report using the Gemini API.
4.  Save the report to the specified `SAVE_PATH` or the default location (`outputs/cambios-<username>-<date>.md`).

## Customization

You can customize the following in your `.env` file:

- **`PROMPT_TEMPLATE`**: Change the prompt to alter the style and content of the generated report.
- **`SAVE_PATH`**: Specify a different absolute path to save the output file.
- **`USERNAME_GIT`**: Change the username used in the default output file name.
- **`SINCE_DATE`**: Adjust the timeframe for the git logs.

---
