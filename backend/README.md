
# 🧠 Memory Simulation Backend

This repository contains the Django-based backend for the Memory Simulation narrative game. It provides REST API endpoints for retrieving static story questions and paragraphs, and serves as the foundation for future integration of RAG, LLM, and image generation modules.

---

## 🚀 Features

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

## 🧩 Project Structure

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

## 🛠️ How to Run Locally

### ✅ Step 1: Clone the Repository

```bash
git clone https://github.com/YOUR_TEAM_NAME/DECO3801---Data-Busters.git
cd DECO3801---Data-Busters
git checkout feature/backend-init
```

> Replace the branch name if using another branch.

---

### ✅ Step 2: Set Up a Python Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate         # Windows: venv\Scripts\activate
```

---

### ✅ Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

---

### ✅ Step 4: Run Migrations

```bash
python manage.py migrate
```

---

### ✅ Step 5: Start the Development Server

```bash
python manage.py runserver
```

Then open your browser or use terminal tools like `curl` to test the following round-based endpoints:

---

## 🧪 Pseudo API Endpoints (Round-by-Round)

Each round includes:
1. Year-based background story
2. Ethical yes/no question
3. Branching result based on player choice

---

### 🔗 Web Test Examples

- [http://127.0.0.1:8000/api/storyline/start?year=2035](http://127.0.0.1:8000/api/storyline/start?year=2035)
- [http://127.0.0.1:8000/api/storyline/question?year=2035](http://127.0.0.1:8000/api/storyline/question?year=2035)
- [http://127.0.0.1:8000/api/storyline/choice?year=2035&choice=no](http://127.0.0.1:8000/api/storyline/choice?year=2035&choice=no)

---

### 💻 Terminal Testing

```bash
curl http://127.0.0.1:8000/api/storyline/start?year=2035
curl http://127.0.0.1:8000/api/storyline/question?year=2035
curl http://127.0.0.1:8000/api/storyline/choice?year=2035\&choice=no
```

> Remember to escape `&` when using curl

---

## 🧪 Sample API Output

### `GET /api/storyline/start?year=2037`

```json
{
  "year": 2037,
  "background": "MemoryCloud™, a global memory storage platform, launches permanent consciousness backup in exchange for behavioral data."
}
```

### `GET /api/storyline/question?year=2037`

```json
{
  "year": 2037,
  "question": "Would you upload your memories to the cloud in exchange for convenience?"
}
```

### `GET /api/storyline/choice?year=2037&choice=yes`

```json
{
  "year": 2037,
  "choice": "yes",
  "result": "You opt in to the service, gaining instant memory access, but also exposing your thoughts to corporate analytics.",
  "next_year": 2038
}
```

---

## 👥 For Collaborators

- Please create a new branch before developing (e.g., `feature/rag-module`, `feature/llm-api`)
- Make sure to pull latest changes before working
- Don’t commit `venv/` or `.sqlite3` files — they’re excluded via `.gitignore`
- For frontend testing instructions and API usage, see [WIKI API Usage Guide for Frontend](https://github.com/manya-k/DECO3801---Data-Busters/wiki/API-Usage-Guide-for-Frontend)

---

### 🌐 Frontend Integration Notes (CORS)

CORS (Cross-Origin Resource Sharing) has been enabled via `django-cors-headers` in this backend.

Frontend developers can now directly `fetch()` Django API endpoints from React, for example:

```js
fetch("http://127.0.0.1:8000/api/storyline/start?year=2035")
  .then((res) => res.json())
  .then((data) => console.log(data));
```

> No additional proxy settings are required for local development.

---

## 📌 To-Do (Backend Roadmap)

- [ ] RAG embedding + chunk loader
- [ ] LLM story/question generation
- [ ] Timeline & turn loop controller
- [ ] AI image integration (ComfyUI or SD)

---

## 📬 Contact

For questions, contact `@Iris` in Discord or check the `feature/backend-init` branch for updates.
