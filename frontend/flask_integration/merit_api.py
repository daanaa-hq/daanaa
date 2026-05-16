"""
MERIT API Blueprint for Flask
==============================
Drop this file into your Flask project and register the blueprint.

    from flask_integration.merit_api import merit_api_bp
    app.register_blueprint(merit_api_bp, url_prefix='/api')

This connects your existing database to the MERIT React frontend.
"""

from flask import Blueprint, request, jsonify, current_app
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os
import json

merit_api_bp = Blueprint('merit_api', __name__)

# Database connection — reads from DATABASE_URL env var
# Supports: sqlite:///path, postgresql://..., mysql://...
DATABASE_URL = os.environ.get('DATABASE_URL', 'sqlite:///data/merit.db')
engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)

# ---- Helper: serialize org row to dict ----
def org_to_dict(row):
    """Convert a database row to the API response format."""
    programs = []
    if row.get('programs'):
        try:
            programs = json.loads(row['programs'])
        except (json.JSONDecodeError, TypeError):
            programs = [p.strip() for p in str(row['programs']).split(',') if p.strip()]

    leadership = []
    if row.get('leadership'):
        try:
            leadership = json.loads(row['leadership'])
        except (json.JSONDecodeError, TypeError):
            pass

    revenue_trend = []
    if row.get('revenue_trend'):
        try:
            revenue_trend = json.loads(row['revenue_trend'])
        except (json.JSONDecodeError, TypeError):
            pass

    return {
        "id": str(row['id']),
        "name": row['name'],
        "ein": row.get('ein', ''),
        "city": row.get('city', ''),
        "state": row.get('state', ''),
        "category": row.get('category', ''),
        "subcategory": row.get('subcategory', ''),
        "merit_score": int(row['merit_score']) if row.get('merit_score') else 0,
        "revenue": int(row['revenue']) if row.get('revenue') else 0,
        "assets": int(row['assets']) if row.get('assets') else 0,
        "employees": int(row['employees']) if row.get('employees') else 0,
        "founded": int(row['founded']) if row.get('founded') else 0,
        "mission": row.get('mission', ''),
        "programs": programs,
        "leadership": leadership,
        "board_size": int(row['board_size']) if row.get('board_size') else 0,
        "revenue_trend": revenue_trend,
        "program_efficiency": int(row['program_efficiency']) if row.get('program_efficiency') else 0,
        "fundraising_ratio": int(row['fundraising_ratio']) if row.get('fundraising_ratio') else 0,
        "operating_reserve": float(row['operating_reserve']) if row.get('operating_reserve') else 0,
        "transparency_score": int(row['transparency_score']) if row.get('transparency_score') else 0,
    }


# ---- ENDPOINTS ----

@merit_api_bp.route('/stats', methods=['GET'])
def get_stats():
    """GET /api/stats — Platform statistics for homepage."""
    session = Session()
    try:
        total_orgs = session.execute(
            text("SELECT COUNT(*) FROM organizations")
        ).scalar() or 0

        total_cats = session.execute(
            text("SELECT COUNT(DISTINCT category) FROM organizations")
        ).scalar() or 0

        states = session.execute(
            text("SELECT COUNT(DISTINCT state) FROM organizations")
        ).scalar() or 0

        return jsonify({
            "total_organizations": int(total_orgs),
            "total_categories": int(total_cats),
            "states_covered": int(states)
        })
    except Exception as e:
        current_app.logger.error(f"Stats error: {e}")
        # Return sensible defaults if DB not initialized
        return jsonify({
            "total_organizations": 0,
            "total_categories": 0,
            "states_covered": 0
        })
    finally:
        session.close()


@merit_api_bp.route('/categories', methods=['GET'])
def get_categories():
    """GET /api/categories — List all categories with org counts."""
    session = Session()
    try:
        result = session.execute(text("""
            SELECT 
                COALESCE(category, 'uncategorized') as id,
                COALESCE(subcategory, 'Uncategorized') as name,
                COUNT(*) as org_count
            FROM organizations
            GROUP BY category, subcategory
            ORDER BY org_count DESC
        """))

        # Map to frontend icon names
        icon_map = {
            'education': 'graduation-cap',
            'health': 'heart-pulse',
            'human-services': 'hands-helping',
            'arts': 'palette',
            'environment': 'leaf',
            'community': 'users',
            'animals': 'paw',
            'international': 'globe',
            'religion': 'church',
            'civil-rights': 'scale',
        }

        categories = []
        for row in result.mappings():
            cat_id = row['id'].lower().replace(' ', '-').replace('&', '').replace(',', '')
            categories.append({
                "id": cat_id,
                "name": row['name'],
                "icon": icon_map.get(cat_id, 'users'),
                "org_count": int(row['org_count'])
            })

        return jsonify(categories)
    except Exception as e:
        current_app.logger.error(f"Categories error: {e}")
        return jsonify([])
    finally:
        session.close()


@merit_api_bp.route('/organizations', methods=['GET'])
def get_organizations():
    """GET /api/organizations — List with search, filter, sort, pagination."""
    session = Session()
    try:
        # Parse query params
        search = request.args.get('search', '').strip()
        category = request.args.get('category', '').strip()
        sort = request.args.get('sort', 'merit_score')
        page = max(1, int(request.args.get('page', 1)))
        per_page = min(100, max(1, int(request.args.get('per_page', 9))))

        # Build WHERE clauses
        where_clauses = []
        params = {}

        if search:
            where_clauses.append("""
                (name ILIKE :search OR city ILIKE :search OR ein ILIKE :search
                 OR subcategory ILIKE :search)
            """)
            params['search'] = f'%{search}%'

        if category:
            where_clauses.append("category = :category")
            params['category'] = category

        where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

        # Count total
        count_sql = f"SELECT COUNT(*) FROM organizations WHERE {where_sql}"
        total = session.execute(text(count_sql), params).scalar() or 0

        # Sort mapping
        sort_map = {
            'merit_score': 'merit_score DESC',
            'name': 'name ASC',
            'revenue': 'revenue DESC',
        }
        order_by = sort_map.get(sort, 'merit_score DESC')

        # Fetch page
        offset = (page - 1) * per_page
        query_sql = f"""
            SELECT * FROM organizations
            WHERE {where_sql}
            ORDER BY {order_by}
            LIMIT :limit OFFSET :offset
        """
        params['limit'] = per_page
        params['offset'] = offset

        result = session.execute(text(query_sql), params)
        organizations = [org_to_dict(row._mapping) for row in result]

        total_pages = (int(total) + per_page - 1) // per_page

        return jsonify({
            "organizations": organizations,
            "total": int(total),
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages
        })

    except Exception as e:
        current_app.logger.error(f"Organizations list error: {e}")
        return jsonify({
            "organizations": [],
            "total": 0,
            "page": 1,
            "per_page": 9,
            "total_pages": 0
        }), 500
    finally:
        session.close()


@merit_api_bp.route('/organizations/<id>', methods=['GET'])
def get_organization(id):
    """GET /api/organizations/:id — Single organization detail."""
    session = Session()
    try:
        result = session.execute(
            text("SELECT * FROM organizations WHERE id = :id"),
            {"id": id}
        )
        row = result.mappings().first()

        if not row:
            return jsonify({"error": "Organization not found"}), 404

        return jsonify(org_to_dict(row))

    except Exception as e:
        current_app.logger.error(f"Organization detail error: {e}")
        return jsonify({"error": "Internal server error"}), 500
    finally:
        session.close()


# ---- Admin endpoints (optional, for data management) ----

@merit_api_bp.route('/organizations/<id>', methods=['PUT'])
def update_organization(id):
    """PUT /api/organizations/:id — Update an organization."""
    session = Session()
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Build update SQL dynamically
        allowed_fields = [
            'name', 'ein', 'city', 'state', 'category', 'subcategory',
            'merit_score', 'revenue', 'assets', 'employees', 'founded',
            'mission', 'programs', 'leadership', 'board_size',
            'revenue_trend', 'program_efficiency', 'fundraising_ratio',
            'operating_reserve', 'transparency_score'
        ]

        updates = []
        params = {"id": id}

        for field in allowed_fields:
            if field in data:
                updates.append(f"{field} = :{field}")
                # JSON-encode lists/objects
                if field in ('programs', 'leadership', 'revenue_trend') and not isinstance(data[field], str):
                    params[field] = json.dumps(data[field])
                else:
                    params[field] = data[field]

        if not updates:
            return jsonify({"error": "No valid fields to update"}), 400

        update_sql = f"UPDATE organizations SET {', '.join(updates)} WHERE id = :id"
        session.execute(text(update_sql), params)
        session.commit()

        return jsonify({"success": True})

    except Exception as e:
        session.rollback()
        current_app.logger.error(f"Update error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@merit_api_bp.route('/organizations/bulk', methods=['POST'])
def bulk_import():
    """POST /api/organizations/bulk — Import multiple organizations."""
    session = Session()
    try:
        data = request.get_json()
        organizations = data.get('organizations', [])

        if not organizations:
            return jsonify({"error": "No organizations provided"}), 400

        inserted = 0
        errors = []

        for org in organizations:
            try:
                session.execute(text("""
                    INSERT INTO organizations 
                    (id, name, ein, city, state, category, subcategory, merit_score,
                     revenue, assets, employees, founded, mission, programs, leadership,
                     board_size, revenue_trend, program_efficiency, fundraising_ratio,
                     operating_reserve, transparency_score, created_at, updated_at)
                    VALUES (:id, :name, :ein, :city, :state, :category, :subcategory,
                            :merit_score, :revenue, :assets, :employees, :founded,
                            :mission, :programs, :leadership, :board_size, :revenue_trend,
                            :program_efficiency, :fundraising_ratio, :operating_reserve,
                            :transparency_score, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    ON CONFLICT (id) DO UPDATE SET
                        name = EXCLUDED.name,
                        ein = EXCLUDED.ein,
                        city = EXCLUDED.city,
                        state = EXCLUDED.state,
                        category = EXCLUDED.category,
                        subcategory = EXCLUDED.subcategory,
                        merit_score = EXCLUDED.merit_score,
                        revenue = EXCLUDED.revenue,
                        assets = EXCLUDED.assets,
                        employees = EXCLUDED.employees,
                        founded = EXCLUDED.founded,
                        mission = EXCLUDED.mission,
                        programs = EXCLUDED.programs,
                        leadership = EXCLUDED.leadership,
                        board_size = EXCLUDED.board_size,
                        revenue_trend = EXCLUDED.revenue_trend,
                        program_efficiency = EXCLUDED.program_efficiency,
                        fundraising_ratio = EXCLUDED.fundraising_ratio,
                        operating_reserve = EXCLUDED.operating_reserve,
                        transparency_score = EXCLUDED.transparency_score,
                        updated_at = CURRENT_TIMESTAMP
                """), {
                    "id": org.get('id'),
                    "name": org.get('name'),
                    "ein": org.get('ein', ''),
                    "city": org.get('city', ''),
                    "state": org.get('state', ''),
                    "category": org.get('category', ''),
                    "subcategory": org.get('subcategory', ''),
                    "merit_score": org.get('merit_score', 0),
                    "revenue": org.get('revenue', 0),
                    "assets": org.get('assets', 0),
                    "employees": org.get('employees', 0),
                    "founded": org.get('founded', 0),
                    "mission": org.get('mission', ''),
                    "programs": json.dumps(org.get('programs', [])) if isinstance(org.get('programs'), list) else org.get('programs', '[]'),
                    "leadership": json.dumps(org.get('leadership', [])) if isinstance(org.get('leadership'), list) else org.get('leadership', '[]'),
                    "board_size": org.get('board_size', 0),
                    "revenue_trend": json.dumps(org.get('revenue_trend', [])) if isinstance(org.get('revenue_trend'), list) else org.get('revenue_trend', '[]'),
                    "program_efficiency": org.get('program_efficiency', 0),
                    "fundraising_ratio": org.get('fundraising_ratio', 0),
                    "operating_reserve": org.get('operating_reserve', 0),
                    "transparency_score": org.get('transparency_score', 0),
                })
                inserted += 1
            except Exception as e:
                errors.append({"org": org.get('name', 'unknown'), "error": str(e)})

        session.commit()

        return jsonify({
            "inserted": inserted,
            "errors": errors,
            "total": len(organizations)
        })

    except Exception as e:
        session.rollback()
        current_app.logger.error(f"Bulk import error: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()
