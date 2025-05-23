# Sense Server

## Prerequisites

Before you begin, ensure you have the following installed:

1.  **Python:** Version 3.8 or higher is recommended. You can download it from [python.org](https://www.python.org/downloads/).
2.  **`uv`:** This project uses `uv` for package and environment management. Install it by following the official instructions: [https://github.com/astral-sh/uv#installation](https://github.com/astral-sh/uv#installation)
    * **macOS / Linux:**
        ```bash
        curl -LsSf [https://astral.sh/uv/install.sh](https://astral.sh/uv/install.sh) | sh
        ```
    * **Windows:**
        ```powershell
        powershell -c "irm [https://astral.sh/uv/install.ps1](https://astral.sh/uv/install.ps1) | iex"
        ```
    * Verify the installation:
        ```bash
        uv --version
        ```

## Setup Instructions

Follow these steps to get your development environment set up:

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/kamilaarsil/server_iot.git
    cd server_iot
    ```

2.  **Obtain Required Files (Manual Step):**
    * **`models/` Folder:** This project requires a `models/` folder containing necessary model files. These files are **not** included in the git repository (as specified in `.gitignore`).
        * **Action:** You **must** request the `models.zip` (or similar archive) file via WhatsApp from kamila.
        * **Placement:** Once received, extract the archive and place the resulting `models/` folder directly into the **root directory** of this project (the same directory where this `README.md` file is located).
    * **Database File (`*.db` / `*.sqlite3`):** The project might require a specific database file (`.db` or `.sqlite3`) to run correctly, especially if it contains pre-existing data or schemas. This file is also **not** included in the repository.
        * **Action (If needed):** If instructed or if the application fails to start without it, request the database file (e.g., `database.db` or `app.sqlite3`) via WhatsApp from kamila.
        * **Placement:** Place the received database file directly into the **root directory** of the project.

3.  **Install Dependencies:**
    `uv` will handle the creation of a virtual environment and installation of dependencies based on the `pyproject.toml` file. Navigate to the project's root directory in your terminal and run:
    ```bash
    uv install
    uv sync
    uv pip install tensorflow
    ```
    This command reads the `pyproject.toml` file, creates a virtual environment (usually in `.venv`), and installs all the required packages listed in `pyproject.toml` or `uv.lock`.

## Running the Application

Once the setup is complete and you have placed the required `models/` folder (and database file, if necessary) in the root directory:

1.  Make sure you are in the project's root directory in your terminal.
2.  Run the main application script using `uv`:
    ```bash
    uv run main.py
    ```

This command tells `uv` to execute the `main.py` script within the managed virtual environment. Your application should now start.