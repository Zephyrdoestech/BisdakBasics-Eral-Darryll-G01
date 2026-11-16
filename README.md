# Bisdak Basics

Bisdak Basics is a Django web application for learning practical Cebuano/Bisaya. It will support learner and administrator accounts, situational lessons, a searchable phrasebook, assessments, and progress monitoring.

## Current checkpoint

The current checkpoint includes a responsive public homepage, learner registration and login/logout, role-protected starter dashboards, and a responsive profile page. Users can update their name, email, contact number, location, and learning goal. Dashboard progress and learning content are shown as honest empty states until those features are added. Lessons, phrasebook, and quizzes remain future checkpoints.

## Requirements

- Python 3.10 or newer
- PostgreSQL 14 or newer

SQLite is not configured. The project requires a PostgreSQL `DATABASE_URL`.

## Local setup

1. Create and activate a virtual environment:

   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```

2. Install dependencies:

   ```powershell
   python -m pip install -r requirements.txt
   ```

3. Create a PostgreSQL database named `bisdak_basics` (or choose another name).

4. Copy `.env.example` to `.env` and set `SECRET_KEY` and `DATABASE_URL` to your local values.

5. Apply Django's initial migrations and start the development server:

   ```powershell
   python manage.py migrate
   python manage.py runserver
   ```

The site will be available at <http://127.0.0.1:8000/>.

## Deploy on Render

Connect this GitHub repository to a Render Python web service and set:

- Build command: `bash build.sh`
- Start command: `python -m gunicorn config.wsgi:application --log-file -`

Configure these environment variables in the Render service settings. Do not commit production values:

- `SECRET_KEY`: generate a new secret in Render.
- `DEBUG`: `False`
- `DATABASE_URL`: your PostgreSQL URL. For Supabase, use its shared pooler URL; session mode on port 5432 works with this project's persistent database connections.
- `DB_CONN_MAX_AGE`: `60` (optional; this is already the default).
- `ALLOWED_HOSTS`: only needed for custom domains; the Render hostname is added automatically.

The build script collects static files and applies pending migrations during deployment. After the first successful deploy, run `python manage.py createsuperuser` in the Render Shell to create an administrator account.

For Supabase, copy a shared pooler URL from the project's **Connect** panel. Render's guide explains the connection modes and notes that direct Supabase connections can have IPv6 reachability issues: <https://render.com/articles/how-to-connect-a-render-service-to-supabase-postgres>.

## Repository naming

The requested repository naming pattern is `SystemName-Lastname-Firstname-Section`. The local folder is currently named `BisdakBasics`; rename the GitHub repository to the required pattern when the section value is known. Keep `.env`, virtual environments, and Python cache files out of commits.
