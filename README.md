# Memory Futures Game

Instructions on running the project

#  Setup Instructions

## Front End:
Make sure you have the latest versions of Node and npm:

```bash
node -v
npm -v
```

### If versions are fine, run:
```bash
brew install node
```

1. On MacOS run```brew install node```. 
On another OS: follow the instructions on [Node's website](https://nodejs.org/en/download)
   
Steps to follow everytime a new branch is pulled:

2. clone the repository if not already cloned: 
```https://github.com/manya-k/DECO3801---Data-Busters.git```
3. ```cd frontend/src```
4. ```npm install```
5. ```npm run dev``` -- to actually run the game

## Back End: 

## Features

- Django 4.x backend scaffolded and structured for local development
- Static story content and yes/no questions (starting from year 2035)
- One working API endpoints:
  - `/api/static-story?year=YYYY` – returns full round data (background, question, yes/no outcomes)
- Modular folder structure for future components:
  - `rag/` for retrieval-augmented generation
  - `llm/` for local LLM integration
  - `images/` for image generation (e.g. via ComfyUI)
  - `core/` for turn logic and timeline control

---

##  Project Structure

```
├── api/                    # API endpoints and static data
│   ├── views.py
│   ├── urls.py
│   └── data/
│       ├── static_questions.json
│       └── static_stories.json
├── core/                   # (Optional) Turn system, gameplay routes
├── llm/                    # Local LLM call interface (planned)
├── rag/                    # RAG logic and prompt templates (planned)
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

---

## Prerequisites (System-level Dependencies)

These are OS-level packages required by document parsing libraries:

### macOS (Homebrew)
```bash
brew update
brew install libmagic
# Recommended for robust PDF/Image parsing:
brew install poppler tesseract
```

### Windows

#### Option 1: Using Chocolatey (Recommended)
```cmd
# Install Chocolatey if not already installed (run as Administrator)
# Visit https://chocolatey.org/install for installation instructions

# Install required packages
choco install python3
choco install poppler
choco install tesseract
```

#### Option 2: Manual Installation
1. **Python**: Download from https://www.python.org/downloads/windows/
2. **Poppler**: Download from https://github.com/oschwartz10612/poppler-windows/releases/
   - Extract to `C:\Program Files\poppler-xx\` and add `C:\Program Files\poppler-xx\Library\bin\` to PATH
3. **Tesseract**: Download from https://github.com/UB-Mannheim/tesseract/wiki
   - Install and add installation directory to PATH (usually `C:\Program Files\Tesseract-OCR\`)
4. **libmagic**: Will be automatically installed via pip when running `pip install -r requirements.txt`

#### Verify Installation (Windows)
```cmd
python --version
pdftoppm -h
tesseract --version
```

---

## 🛠️ How to Run Locally

### Ollama Installation & Setup

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
- **Desktop App**: Open the Ollama desktop application, or
- **Command Line**: Run `ollama serve` in terminal/command prompt

---

### Step 1: Clone the Repository

```bash
git clone https://github.com/manya-k/DECO3801---Data-Busters.git
cd DECO3801---Data-Busters
git checkout feature/backend-init
```

> Replace the branch name if using another branch.

---

### Step 2: Set Up a Python Virtual Environment

#### macOS/Linux
```bash
python3 -m venv venv
source venv/bin/activate
```

#### Windows
```cmd
# Using Command Prompt
python -m venv venv
venv\Scripts\activate

# Using PowerShell
python -m venv venv
venv\Scripts\Activate.ps1
```

> **Note for Windows**: If you encounter execution policy issues in PowerShell, run:
> ```powershell
> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
> ```

---

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
pip install -U pip wheel setuptools
```

> **Note**: The `requirements.txt` file automatically installs the correct `python-magic` package for your platform:
> - **macOS/Linux**: `python-magic` 
> - **Windows**: `python-magic-bin` (includes required libmagic binaries)

---

### Step 4: Download NLTK Data & Setup (first-time only)

#### macOS
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

---

### Step 5: Verify Vector Store setup (optional)

#### Verify Setup (All Platforms)
```bash
# macOS/Linux
ls -lah backend/rag/db/faiss_db

# Windows
dir backend\rag\db\faiss_db
```
Should contain `index.faiss` and `index.pkl`

#### Quick Retrieval Test

**macOS/Linux:**
```bash
python manage.py shell -c "
from rag.retrieve import retrieve_chunks;
result = retrieve_chunks('sleep memory consolidation')
for chunk in result:
    for key, value in chunk.items():
        print(f'{key}: {value}\n')
    print('\n---\n')
"
```

**Windows:**
```cmd
python manage.py shell -c "from rag.retrieve import retrieve_chunks; print(retrieve_chunks('sleep memory consolidation')[:1])"
```

---

Now make sure to navigate to the backend directory:

**macOS/Linux:**
```bash
cd backend
```

**Windows:**
```cmd
cd backend
```

### Step 6: Set up database

**macOS/Linux:**
```bash
brew install postgresql
brew services start postgresql
```
**Windows:**
- Download from: https://www.postgresql.org/download/windows/
- After installation, set environment path:
```bash
C:\Program Files\PostgreSQL\18\bin
```

### Step 7: Create DB user

**macOS/Linux:**
```bash
psql postgres
```
**Windows:**
Note that the `createdb` command may or may not be necessary to set up the database on your device.
```bash
psql -U postgres
```

```bash
# inside the shell, enter
CREATE DATABASE memorysim_db;
CREATE USER memorysim_user WITH PASSWORD 'password123';
GRANT ALL PRIVILEGES ON DATABASE memorysim_db TO memorysim_user;
\c memorysim_db;
GRANT ALL ON SCHEMA public TO memorysim_user;
\q
```
extra step for Windows:
- Use default setup and remember username/password, enable pgadmin: memorysim_user > properties > privelages > enable all (superuser)


### Step 8: Run migration

``` bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser # only if you want to access the db interface
```
then follow the instructions, you need to set name, email and pwd for admin access, later you can visit http://127.0.0.1:9000/admin/, login and view data

Initialize Database Content (First-time only, after database migration, populate initial content)
```bash
# Create world background story
python create_background.py

# Load default query keywords (if keywords file exists)
python load_keywords_script.py
```


### Step 9: Set up bg manager

**macOS/Linux:**
``` bash
brew install redis
```

**Windows:**
- Download Redis from this community-maintained build: https://github.com/microsoftarchive/redis/releases
- Choose Redis-x64-3.2.100.msi and install

**macOS/Linux:**
``` bash
redis-server
```

**Windows:**
```bash
redis-server.exe --port 6380 --bind 127.0.0.1
```
### Step 10: create 3 worker (each from a different terminal and 'cd backend' in the (venv))
``` bash
python manage.py rundramatiq --queues default --processes 1 --threads 1
python manage.py rundramatiq --queues image_queue --processes 1 --threads 1
python manage.py rundramatiq --queues llm_queue --processes 1 --threads 1
```

### Step 11: Start the ComfyUI Server
- download ComfyUI https://www.comfy.org/download
- download dreamshaper model ver 7 https://civitai.com/models/4384?modelVersionId=109123
- put the model under `ComfyUI/models/checkpoints`
- starts ComfyUI server, make sure it is running at port 8000, if default not 8000, run it from terminal, switch to port 8000
    ```bash
    cd /path/to/ComfyUI
    python main.py --port 8000
    ```

### Step 12: Start the Development Server at port 9000

```bash
python manage.py runserver 9000
```

Then open your browser or use terminal tools like `curl` to test the following round-based endpoints:

---

## Pseudo API Endpoints (Round-by-Round)

Each round includes:
1. Year-based background story
2. Ethical yes/no question
3. Branching result based on player choice

## Testing the RAG retrieval API

MacOS/Linux: Try this `curl` query to test the RAG chunk retrieval API once the backend is running.

```bash
curl --header "Content-Type: application/json" \
--request POST \
--data '{ "query_text": "what is the future of memory", "keywords": ["future", "memory"]}' \
http://127.0.0.1:9000/api/rag/retrieve
```

To test fun facts API:

On MacOS/Linux:
```bash
curl --header "Content-Type: application/json" \
--request POST \
http://127.0.0.1:9000/api/rag/fun_facts
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
- For frontend testing instructions and API usage, see [WIKI API Usage Guide for Frontend](https://github.com/manya-k/DECO3801---Data-Busters/wiki/API-Usage-Guide-for-Frontend)

---

### Frontend Integration Notes (CORS)

CORS (Cross-Origin Resource Sharing) has been enabled via `django-cors-headers` in this backend.

Frontend developers can now directly `fetch()` Django API endpoints from React, for example:

```js
fetch("http://127.0.0.1:9000/api/storyline/start?year=2035")
  .then((res) => res.json())
  .then((data) => console.log(data));
```

> No additional proxy settings are required for local development.

---
