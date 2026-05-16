# MERIT Frontend — Integration Guide

## What You're Getting

A world-class React frontend for your MERIT nonprofit intelligence platform. It connects to your existing Python/Flask backend via REST API calls.

## File Structure

```
merit-frontend-package/
├── dist/                          # BUILT FRONTEND FILES (deploy these)
│   ├── index.html                 # Single entry point
│   ├── assets/                    # JS, CSS, fonts
│   └── images/                    # Static images
├── src/                           # Full source code (for modifications)
├── flask_integration/
│   ├── merit_api.py               # Flask Blueprint with all API endpoints
│   ├── init_db.sql                # Database schema
│   ├── seed_data.py               # Load your existing data
│   └── update_daemon.py          # Daily update scaffold
├── API_SPEC.md                    # Complete API specification
└── INTEGRATION_README.md          # This file
```

## Quick Start (5 Steps)

### Step 1: Copy built files to your Flask static folder

```bash
# On your server at /home/meritgiving
cp -r dist/* /home/meritgiving/web/static/
```

### Step 2: Install the Flask API Blueprint

Copy `flask_integration/merit_api.py` into your project and register it:

```python
# In your app.py or wherever you create your Flask app
from flask_integration.merit_api import merit_api_bp

app.register_blueprint(merit_api_bp, url_prefix='/api')
```

### Step 3: Serve the SPA from Flask

Add this route to handle React Router (all paths serve index.html):

```python
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    if path.startswith('api/'):
        return jsonify({"error": "API route not found"}), 404
    # Serve index.html for all routes (React Router handles client-side)
    return send_from_directory('web/static', 'index.html')
```

### Step 4: Set environment variable for API URL

Create a `.env` file in your project root:

```bash
# /home/meritgiving/.env
MERIT_API_URL=/api
DATABASE_URL=sqlite:///data/merit.db
# Or for PostgreSQL:
# DATABASE_URL=postgresql://user:pass@localhost/merit
```

### Step 5: Initialize the database

```bash
cd /home/meritgiving
python flask_integration/init_db.py
python flask_integration/seed_data.py --source your_existing_data.csv
```

## API Endpoints Required

Your backend must implement these endpoints (see `API_SPEC.md` for full details):

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/organizations` | List orgs (with search, filter, sort, paginate) |
| GET | `/api/organizations/:id` | Single org detail |
| GET | `/api/categories` | List all categories |
| GET | `/api/stats` | Platform statistics |

## Connecting to Your Existing Database

The `merit_api.py` blueprint uses SQLAlchemy and can connect to:
- **SQLite** (default for development)
- **PostgreSQL** (recommended for production)
- **MySQL**

Just set `DATABASE_URL` in your environment. The schema in `init_db.sql` creates the tables the frontend expects.

## Migrating Your Existing Data

If you have data in CSV, JSON, or another database:

1. Export your existing nonprofit data to CSV with these columns:
   `id, name, ein, city, state, category, subcategory, merit_score, revenue, assets, employees, founded, mission, programs, leadership, board_size, revenue_trend, program_efficiency, fundraising_ratio, operating_reserve, transparency_score`

2. Run the seed script:
   ```bash
   python flask_integration/seed_data.py --source /path/to/your/data.csv
   ```

## Daily Updates

The `update_daemon.py` provides a scaffold for your daily data pipeline. It:
1. Fetches new IRS data
2. Validates records
3. Updates the database
4. Logs errors to `MERIT_ERROR_LOG.md`

Integrate it with your existing `merit_daemon.py` or run it via cron:

```bash
# Add to crontab
crontab -e
# Add this line for daily 3am updates:
0 3 * * * cd /home/meritgiving && python flask_integration/update_daemon.py >> logs/daily_update.log 2>&1
```

## CORS Configuration

If your frontend and API are on different domains, enable CORS:

```bash
pip install flask-cors
```

```python
from flask_cors import CORS
CORS(app, origins=["https://yourdomain.com"])
```

## Need Help?

- **API issues**: Check `API_SPEC.md` for request/response formats
- **Database issues**: Verify `init_db.sql` schema matches your data
- **Frontend issues**: Check browser DevTools Network tab for API calls
