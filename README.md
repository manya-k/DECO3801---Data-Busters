# Future of Memory

Interested to know what how memories will be used, modified and treated in the future?

# Setup Instructions

Follow these instructions to set up both the frontend and backend to run the project.

First ensure you have cloned the repository if not already cloned, from `https://github.com/manya-k/DECO3801---Data-Busters.git`

## Frontend Setup

1. Make sure you have the latest versions of Node and npm:
   ```
   node -v
   npm -v
   ```
   If not, you'll need to install them. On MacOS run
   ```bash
   brew install node
   ```
   On another OS: follow the instructions on [Node's website](https://nodejs.org/en/download).

Steps to follow everytime a new branch is pulled:

2. Run these commands:
   ```
   cd frontend/src
   npm install
   npm run dev
   npm run dev -- --host # to host on Mac; or
   npm run dev --host # to host on Windows
   ```
3. Navigate to one of the displayed `localhost` links to open the game in your browser.

## Backend

### Features

- Django 4.x backend scaffolded and structured for local development
- Static story content and yes/no questions (starting from year 2035)
- One working API endpoints:
  - `/api/static-story?year=YYYY` – returns full round data (background, question, yes/no outcomes)
- Modular folder structure for future components:
  - `rag/` for retrieval-augmented generation
  - `llm/` for local LLM integration
  - `images/` for image generation (e.g. via ComfyUI)
  - `core/` for turn logic and timeline control

### Project Structure

```
├── api/                    # API endpoints and static data
│   ├── views.py
│   ├── urls.py
│   └── data/
│       ├── static_questions.json
│       └── static_stories.json
├── core/                   # (Optional) Turn system, gameplay routes
├── llm/                    # Local LLM call interface
├── rag/                    # RAG logic and prompt templates
├── images/                 # Image generation script placeholder
├── memory_sim/             # Django settings and config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── templates/              # (Optional) Django templates if needed
├── manage.py               # Django command line runner
├── requirements.txt        # Dependencies list
├── .gitignore              # Files to be ignored by git
```

### Prerequisites (System-level Dependencies)

#### Install Redis

**macOS/Linux:**

```bash
brew install redis
```

**Windows:**

- Download Redis from this community-maintained build: https://github.com/microsoftarchive/redis/releases
- Choose Redis-x64-3.2.100.msi and install

#### OS-level packages required by document parsing libraries

#### macOS (Homebrew)

```bash
brew update
brew install libmagic
```

#### Windows

##### Option 1: Using Chocolatey (Recommended)

```cmd
# Install Chocolatey if not already installed (run as Administrator)
# Visit https://chocolatey.org/install for installation instructions

# Install required packages
choco install python3
choco install poppler
choco install tesseract
```

##### Option 2: Manual Installation

1. **Python**: Download from https://www.python.org/downloads/windows/
2. **Poppler**: Download from https://github.com/oschwartz10612/poppler-windows/releases/
   - Extract to `C:\Program Files\poppler-xx\` and add `C:\Program Files\poppler-xx\Library\bin\` to PATH
3. **Tesseract**: Download from https://github.com/UB-Mannheim/tesseract/wiki
   - Install and add installation directory to PATH (usually `C:\Program Files\Tesseract-OCR\`)
4. **libmagic**: Will be automatically installed via pip when running `pip install -r requirements.txt`

##### Verify Installation (Windows)

```cmd
python --version
pdftoppm -h
tesseract --version
```

### Step 1: Ollama Installation & Setup

First ensure you have Ollama installed:

#### macOS/Linux

- Download from https://ollama.com/download/
- You may need to open the app the first time to install the command-line tools

#### Windows

- Download the Windows installer from https://ollama.com/download/
- Run the installer and follow the setup wizard
- The CLI tools will be automatically added to your PATH

#### Verify Installation (All Platforms)

Check that the CLI tools are installed properly:

```bash
ollama --version
```

Should display a version number.

#### Download Required Models

**Essential Models:**
```bash
ollama pull phi3:3.8b          # Default fallback model for all tasks
ollama pull nomic-embed-text   # Text embedding for RAG
ollama pull gemma3:1b-it-qat   # Lightweight model for rag_preprocess and image text generation
```

> **Note for Low-Performance Computers**: If your computer doesn't have enough resources, you can skip the optional models. The system will automatically use `phi3:3.8b` as a fallback for all tasks.

**Performance-Optimized Models:**
```bash
ollama pull qwen3:4b           # Specialized model for scenario generation
```
> 

#### Start Ollama Server

- **Desktop App**: Open the Ollama desktop application; or
- **Command Line**: Run `ollama serve` in terminal/command prompt

### Step 2: ComfyUI Installation & Setup
- download ComfyUI from https://www.comfy.org/download
- download `dreamshaper v7` from https://civitai.com/models/4384?modelVersionId=109123
- place the model under `ComfyUI/models/checkpoints`
- start the ComfyUI server, make sure it is running at port 8000 (should be the default), if default not 8000, switch to port 8000
    ```bash
    cd /path/to/ComfyUI
    python main.py --port 8000
    ```

### Step 3: Set Up a Python Virtual Environment

Create the virtual environment from the project root.

#### macOS/Linux

> If you want to use the existing `tasks.json` file to run the project using VSCode Tasks, the
> virtual environment should be made in the project root.

```bash
python3 -m venv .venv
source .venv/bin/activate
```

#### Windows

```cmd
# Using Command Prompt
python -m venv .venv
.venv\Scripts\activate

# Using PowerShell
python -m venv .venv
.venv\Scripts\Activate.ps1

> If using VSCode, you may want to add this virtual environment as a Python Environment in the UI so
> it will be activated on startup.
```

> **Note for Windows**: If you encounter execution policy issues in PowerShell, run:
>
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

### Step 4: Install Dependencies

Run these commands from the `backend` folder.

```bash
pip install -r requirements.txt
pip install -U pip wheel setuptools
```

> **Note**: The `requirements.txt` file automatically installs the correct `python-magic` package for your platform:
>
> - **macOS/Linux**: `python-magic`
> - **Windows**: `python-magic-bin` (includes required libmagic binaries)

---

### Step 5: Download NLTK Data & Setup (first-time only)

#### macOS

You may need to replace 3.12 with your Python installation version.

```bash
# Fix certificates
/Applications/Python\ 3.12/Install\ Certificates.command
# Download NLTK data
python -m nltk.downloader punkt punkt_tab averaged_perceptron_tagger_eng
```

#### Windows

```cmd
# Download NLTK data (no certificate fixing needed)
python -m nltk.downloader punkt punkt_tab averaged_perceptron_tagger_eng
```

#### Verify NLTK Installation (All Platforms)

```bash
python - <<'PY'
from nltk.tokenize import sent_tokenize
print(sent_tokenize("Hello world. This is a test."))
print("NLTK OK")
PY
```

**For Windows Command Prompt users**, use this alternative verification:

```cmd
python -c "from nltk.tokenize import sent_tokenize; print(sent_tokenize('Hello world. This is a test.')); print('NLTK OK')"
```

### Step 6: Set up database

**macOS/Linux:**

```bash
brew install postgresql
brew services start postgresql
```

**Windows:**

- Download from: https://www.postgresql.org/download/windows/
- After installation, set environment path (may need to change the 18 depending on your version):

```
C:\Program Files\PostgreSQL\18\bin
```

### Step 7: Create DB user

**macOS/Linux:**
```bash
psql postgres
```
**Windows:**
```bash
psql -U postgres
```

```sql
# inside the shell, enter
CREATE DATABASE memorysim_db;
CREATE USER memorysim_user WITH PASSWORD 'password123';
GRANT ALL PRIVILEGES ON DATABASE memorysim_db TO memorysim_user;
\c memorysim_db;
GRANT ALL ON SCHEMA public TO memorysim_user;
\q
```
extra step for Windows:
- Use default setup and remember username/password, enable pgadmin: 
  memorysim_user > properties > privelages > enable all (superuser)

### Step 8: Run migration

```bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser # only if you want to access the db interface
```

If creating a superuser, follow the instructions given. You need to enter your name, email and password
for admin access. Later, you can visit `http://127.0.0.1:9000/admin/` to login and view data in the
database.

**First time only, after database migration:**

Initialise database content:

```bash
# Create world background story
python create_background.py

# Load default query keywords (if keywords file exists)
python load_keywords_script.py
```

**VSCode tasks**

If using VSCode, the following commands to run the project can be run automatically from the Command
Palette.

- To run the project, run "Tasks: Run Task" > "Run project".
- To terminate the project, run "Tasks: Terminate Task" > "All tasks".

### Step 9: Start background manager

Start the redis server:

**macOS/Linux:**

```bash
redis-server
```

**Windows:**

```bash
redis-server.exe --port 6380 --bind 127.0.0.1
```

### Step 10: create 3 workers (each from a different terminal)

Ensure your working directory is the `backend` folder, and then:

```bash
python manage.py rundramatiq --queues default --processes 1 --threads 1
python manage.py rundramatiq --queues image_queue --processes 1 --threads 1
python manage.py rundramatiq --queues llm_queue --processes 1 --threads 1
python manage.py rundramatiq --queues llm_scenario --processes 1 --threads 1
```

### Step 11: Start the Development Server at port 9000

Set `UPDATE_RAG` to `False` in `backend/rag/config.py` if you don't want the RAG system to be
updated (updating it takes some time). Note however that you must have some version of the RAG
system set up to run the project.

```bash
python setup_rag.py
python manage.py runserver 0.0.0.0:9000
```

Then open your browser or use terminal tools like `curl` to test the following round-based endpoints:

## Pseudo API Endpoints (Round-by-Round)

Each round includes:

1. Year-based background story
2. Ethical yes/no question
3. Branching result based on player choice

## Testing the RAG system

### Verify existence of RAG files

```bash
# macOS/Linux
ls -lah backend/rag/db/faiss_db

# Windows
dir backend\rag\db\faiss_db
```

Should contain `index.faiss` and `index.pkl`.

### Quick Retrieval Test

**macOS/Linux:**

```bash
python manage.py shell -c "
from rag.retrieve import retrieve_chunks;
result = retrieve_chunks('sleep memory consolidation')
for chunk in result:
    for key, value in chunk.items():
        print(f'{key}: {value}\n')
    print('\n---\n')
```

**Windows:**

```cmd
python manage.py shell -c "from rag.retrieve import retrieve_chunks; print(retrieve_chunks('sleep memory consolidation')[:1])"
```

### RAG API test

**MacOS/Linux:**

Try this `curl` query to test the RAG chunk retrieval API once the backend is running.

```bash
curl --header "Content-Type: application/json" \
--request POST \
--data '{ "query_text": "what is the future of memory", "keywords": ["future", "memory"]}' \
http://127.0.0.1:9000/api/rag/retrieve \
| python -m json.tool
```

### Fun facts API test

On MacOS/Linux:

```bash
curl --header "Content-Type: application/json" \
--request POST \
http://127.0.0.1:9000/api/rag/fun_facts \
| python -m json.tool
```

On Windows:

```
curl.exe -H "Content-Type: application/json" -X POST http://127.0.0.1:9000/api/rag/fun_facts
```

---

## For Collaborators

- Please create a new branch before developing (e.g., `feature/rag-module`, `feature/llm-api`)
- Make sure to pull latest changes before working
- Don’t commit `venv/` or `.sqlite3` files — they’re excluded via `.gitignore`
- For frontend testing instructions and API usage, see [API Usage Guide for Frontend (wiki page)](https://github.com/manya-k/DECO3801---Data-Busters/wiki/API-Usage-Guide-for-Frontend)

### Frontend Integration Notes (CORS)

CORS (Cross-Origin Resource Sharing) has been enabled via `django-cors-headers` in this backend.

Frontend developers can now directly `fetch()` Django API endpoints from React, for example:

```js
fetch("http://127.0.0.1:9000/api/storyline/start?year=2035")
  .then((res) => res.json())
  .then((data) => console.log(data));
```

> No additional proxy settings are required for local development.