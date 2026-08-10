import json
import logging
from typing import List, Optional, Dict, Any
from app.core.config import settings

logger = logging.getLogger(__name__)

try:
    import psycopg2
    from psycopg2.extras import RealDictCursor
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False
    logger.warning("psycopg2 is not installed. Supabase database functionality will be disabled.")


def get_connection():
    if not PSYCOPG2_AVAILABLE:
        raise RuntimeError("psycopg2 module is not installed.")
    if not settings.DATABASE_URL or "[YOUR-PASSWORD]" in settings.DATABASE_URL:
        raise ValueError("DATABASE_URL is not set or still contains placeholder password.")
    
    return psycopg2.connect(settings.DATABASE_URL)


def init_db():
    """Create or update the blogs table and indexes if they do not exist."""
    if not settings.DATABASE_URL or "[YOUR-PASSWORD]" in settings.DATABASE_URL:
        logger.warning("DATABASE_URL is not configured properly. Skipping init_db.")
        return False

    try:
        conn = get_connection()
        with conn:
            with conn.cursor() as cur:
                # Enable pgcrypto extension if needed for gen_random_uuid
                cur.execute("CREATE EXTENSION IF NOT EXISTS \"pgcrypto\";")
                
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS blogs (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        session_id VARCHAR(64) NOT NULL,
                        blog_title TEXT NOT NULL,
                        final_markdown TEXT NOT NULL,
                        mode VARCHAR(32),
                        needs_research BOOLEAN DEFAULT FALSE,
                        sections_count INTEGER DEFAULT 0,
                        plan JSONB,
                        evidence JSONB DEFAULT '[]',
                        image_specs JSONB DEFAULT '[]',
                        logs JSONB DEFAULT '[]',
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                    
                    ALTER TABLE blogs ADD COLUMN IF NOT EXISTS sections_count INTEGER DEFAULT 0;
                    ALTER TABLE blogs ADD COLUMN IF NOT EXISTS logs JSONB DEFAULT '[]';
                    ALTER TABLE blogs ADD COLUMN IF NOT EXISTS plan JSONB;
                    ALTER TABLE blogs ADD COLUMN IF NOT EXISTS evidence JSONB DEFAULT '[]';
                    ALTER TABLE blogs ADD COLUMN IF NOT EXISTS image_specs JSONB DEFAULT '[]';

                    CREATE INDEX IF NOT EXISTS idx_blogs_session_id ON blogs(session_id);
                    CREATE INDEX IF NOT EXISTS idx_blogs_created_at ON blogs(created_at);
                """)
        conn.close()
        logger.info("✅ Database tables and indexes initialized successfully.")
        return True
    except Exception as e:
        logger.error(f"⚠️ Database initialization failed: {e}")
        return False


def save_blog(session_id: str, data: Dict[str, Any]) -> Optional[str]:
    """Insert a blog record and return its generated UUID string."""
    try:
        conn = get_connection()
        
        plan_json = json.dumps(data.get("plan")) if data.get("plan") else None
        evidence_json = json.dumps(data.get("evidence", []))
        image_specs_json = json.dumps(data.get("image_specs", []))
        logs_json = json.dumps(data.get("logs", []))

        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO blogs (
                        session_id, blog_title, final_markdown, mode, needs_research,
                        sections_count, plan, evidence, image_specs, logs
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                    """,
                    (
                        session_id,
                        data.get("blog_title", "Untitled"),
                        data.get("final_markdown", ""),
                        data.get("mode", "closed_book"),
                        data.get("needs_research", False),
                        data.get("sections_count", 0),
                        plan_json,
                        evidence_json,
                        image_specs_json,
                        logs_json,
                    )
                )
                blog_id = str(cur.fetchone()[0])
        conn.close()
        return blog_id
    except Exception as e:
        logger.error(f"Error saving blog to database: {e}")
        return None


def get_blogs_by_session(session_id: str) -> List[Dict[str, Any]]:
    """Retrieve list of blogs generated for a given session_id."""
    try:
        conn = get_connection()
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id::text AS blog_id, session_id, blog_title, created_at::text AS created_at
                    FROM blogs
                    WHERE session_id = %s
                    ORDER BY created_at DESC;
                    """,
                    (session_id,)
                )
                rows = cur.fetchall()
        conn.close()
        return [dict(row) for row in rows]
    except Exception as e:
        logger.error(f"Error fetching blogs by session {session_id}: {e}")
        return []


def get_blog_by_id(blog_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve a single full blog record by UUID."""
    try:
        conn = get_connection()
        with conn:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT id::text AS blog_id, session_id, blog_title, final_markdown,
                           mode, needs_research, sections_count, plan,
                           evidence, image_specs, logs, created_at::text AS created_at
                    FROM blogs
                    WHERE id = %s::uuid;
                    """,
                    (blog_id,)
                )
                row = cur.fetchone()
        conn.close()
        if not row:
            return None
        
        row_dict = dict(row)

        def parse_json_val(val, default):
            if val is None:
                return default
            if isinstance(val, (dict, list)):
                return val
            if isinstance(val, str):
                try:
                    return json.loads(val)
                except Exception:
                    return default
            return default

        return {
            "blog_id": row_dict["blog_id"],
            "session_id": row_dict["session_id"],
            "blog_title": row_dict["blog_title"],
            "final_markdown": row_dict["final_markdown"],
            "mode": row_dict.get("mode", "closed_book"),
            "needs_research": row_dict.get("needs_research", False),
            "sections_count": row_dict.get("sections_count", 0),
            "plan": parse_json_val(row_dict.get("plan"), None),
            "evidence": parse_json_val(row_dict.get("evidence"), []),
            "image_specs": parse_json_val(row_dict.get("image_specs"), []),
            "logs": parse_json_val(row_dict.get("logs"), []),
            "created_at": row_dict["created_at"],
        }
    except Exception as e:
        logger.error(f"Error fetching blog by ID {blog_id}: {e}")
        return None


def delete_blog_by_id(blog_id: str) -> bool:
    """Delete a single blog by UUID."""
    try:
        conn = get_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM blogs WHERE id = %s::uuid;", (blog_id,))
                deleted = cur.rowcount > 0
        conn.close()
        return deleted
    except Exception as e:
        logger.error(f"Error deleting blog {blog_id}: {e}")
        return False


def delete_old_blogs(max_age_minutes: int = 15) -> int:
    """Delete blogs created more than max_age_minutes ago."""
    try:
        conn = get_connection()
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    "DELETE FROM blogs WHERE created_at < NOW() - (%s || ' minutes')::interval;",
                    (str(max_age_minutes),)
                )
                deleted_count = cur.rowcount
        conn.close()
        if deleted_count > 0:
            logger.info(f"🧹 Cleaned up {deleted_count} blogs older than {max_age_minutes} minutes.")
        return deleted_count
    except Exception as e:
        logger.error(f"Error deleting old blogs: {e}")
        return 0
