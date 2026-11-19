# sangamnathA50

## Backend

The Flask API is in `backend/` and uses Supabase for its database.

To run it locally, create `backend/.env` with your Supabase credentials:

```env
SUPABASE_URL=your-project-url
SUPABASE_PUBLISHABLE_KEY=your-publishable-key
```

Then install the dependencies and start the development server:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

The API will be available at `http://127.0.0.1:5000/`. The root endpoint returns a health message; event and registration endpoints are under `/api/`.

The `.env` file is ignored by Git. Configure `SUPABASE_URL` and `SUPABASE_PUBLISHABLE_KEY` in your deployment environment as well.
# sangamnathA50
