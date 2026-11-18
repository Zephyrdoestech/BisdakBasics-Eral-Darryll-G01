# Bisdak Basics

**Learn practical Cebuano. Build real connections.** Bisdak Basics is a Django web app for learning everyday Cebuano (Bisaya), with a friendly, lesson-focused experience guided by Bito the flying fish.

## Live website

Visit **[bisdak-basics.onrender.com](https://bisdak-basics.onrender.com/)**.

## What is implemented

This project is being built incrementally. The current checkpoint includes:

- Public, responsive landing page.
- Learner registration, login, and logout using Django authentication and hashed passwords.
- Role-based learner and administrator dashboards. Dashboard views require login and reject users with the wrong role.
- A private profile page where a signed-in user can view and update their own name, email, contact number, location, learning goal, and bio.
- Administrator lesson and category management, including phrase translations, checkpoint questions, drafts, and native-speaker audio uploads.
- A learner lesson library with phrase-by-phrase audio, local pronunciation recording and replay, saved phrase practice, checkpoint attempts, and lesson completion tied to the learner account.
- PostgreSQL-only database configuration and WhiteNoise static file serving for deployment.

The searchable phrasebook, full quiz and grammar assessment modules, streaks, achievements, learner feedback, summary reports, and completion certificates are future increments.

## Technology

- Python 3.10+
- Django 5.2
- PostgreSQL (including Supabase PostgreSQL)
- Django templates, HTML, and CSS
- Gunicorn and WhiteNoise on Render

SQLite is not supported by the project settings. The app requires a PostgreSQL `DATABASE_URL`.

## Run locally

You need Python and a running PostgreSQL database.

### Windows PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Edit `.env` and set a private `SECRET_KEY` and your PostgreSQL `DATABASE_URL`. Lesson audio uploads work locally through Django's media folder. For production uploads, create a **public** `lesson-audio` bucket in Supabase Storage with a 15 MB file-size limit and audio MIME types enabled, then set its project URL and server-side service role key in `.env`. Never expose the service role key in client code or commit it. For example:

```dotenv
SECRET_KEY=your-long-random-secret
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
DATABASE_URL=postgresql://postgres:your-password@localhost:5432/bisdak_basics
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=your-server-side-service-role-key
SUPABASE_STORAGE_BUCKET=lesson-audio
```

Create the `bisdak_basics` database first, then run:

```powershell
python manage.py migrate
python manage.py runserver
```

Open <http://127.0.0.1:8000/>. Do not commit `.env`; it is ignored by Git. Use a different secret and database credentials for production.

### Useful commands

```powershell
python manage.py check
python manage.py test
python manage.py createsuperuser
```

The superuser receives the administrator role. To review all registered routes, see the `accounts` and `core` URL configurations.

## Deploy on Render

The app is deployed at [https://bisdak-basics.onrender.com/](https://bisdak-basics.onrender.com/). To connect or redeploy it from this Git repository, configure a Render **Web Service** with:

| Setting | Value |
| --- | --- |
| Runtime | Python |
| Build command | `bash build.sh` |
| Start command | `python -m gunicorn config.wsgi:application --bind 0.0.0.0:$PORT --log-file -` |

Set these environment variables in the Render dashboard:

| Variable | Value |
| --- | --- |
| `SECRET_KEY` | Generate a new secret in Render. |
| `DEBUG` | `False` |
| `DATABASE_URL` | A PostgreSQL connection string from your database provider. |
| `DB_CONN_MAX_AGE` | Optional; defaults to `60`. |
| `SUPABASE_URL` | Your Supabase project URL for lesson audio uploads. |
| `SUPABASE_SERVICE_ROLE_KEY` | Server-only service role key used by Django to upload and delete lesson audio. |
| `SUPABASE_STORAGE_BUCKET` | Public Storage bucket name; defaults to `lesson-audio`. |

Render supplies `RENDER_EXTERNAL_HOSTNAME`; the Django settings add it to `ALLOWED_HOSTS` automatically. If using a custom domain, set `ALLOWED_HOSTS` to include that host. Never paste credentials into Git or this README.

`build.sh` installs requirements, collects static files, and applies database migrations. If the database is Supabase, use a connection URL from the Supabase project's **Connect** panel. A session-mode pooler URL is often appropriate for an app host; follow the connection details shown for your Supabase project.

After the first successful deployment, create the administrator account from the Render Shell:

```bash
python manage.py createsuperuser
```

The learner and administrator dashboards are available after login at `/dashboard/learner/` and `/dashboard/admin/`; `/dashboard/` routes each user to the dashboard for their role.

Learners can open published lessons at `/lessons/`. Administrators can manage lessons at `/dashboard/admin/lessons/`; lesson categories can be managed in Django admin. Local audio files are stored under `media/` while `DEBUG=True`.

## Repository safety

Keep `.env`, virtual environments (`.venv/` or `venv/`), Python bytecode, and `__pycache__/` out of commits. Install dependencies from `requirements.txt`.
