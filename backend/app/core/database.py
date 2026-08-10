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


# Cached working URL once a candidate succeeds (avoids re-probing on every call).
_working_url: Optional[str] = None


def _repair_candidates(url: str) -> List[str]:
    """
    Repair common copy-paste mistakes in Supabase connection URLs.

    Some users paste a URL with a stray extra '@segment' in the middle, e.g.:
        postgresql://postgres:pass@generate123@db.<ref>.supabase.co:5432/postgres
    libpq then mis-parses the hostname as "generate123@db.<ref>.supabase.co".

    We return candidate URLs to try, in order of likelihood:
      A) drop the stray middle segment(s),
      B) treat the stray fragment before the host as the real password.
    """
    if "://" not in url:
        return [url]
    scheme, rest = url.split("://", 1)

    # Split on the LAST '@' — everything after it is the true host[:port]/db.
    userinfo_part, at, host = rest.rpartition("@")
    if not at:
        return [url]  # no '@' at all; nothing to repair

    head_segments = userinfo_part.split("@")
    candidates = []

    # A: drop stray fragments — keep the first user[:pass] segment as-is.
    cand_a = f"{scheme}://{head_segments[0]}@{host}"
    if cand_a != url:
        candidates.append(cand_a)

    # B: the last stray fragment is often the real password (the userinfo one
    # may be truncated or junk). Only if it looks like a password.
    if len(head_segments) >= 2:
        stray = head_segments[-1]
        user = head_segments[0].split(":")[0]
        if stray and "/" not in stray and ":" not in stray:
            candidates.append(f"{scheme}://{user}:{stray}@{host}")

    return candidates or [url]


def _try_connect(url: str):
    try:
        return psycopg2.connect(url)
    except Exception:
        # Supabase requires SSL; retry with sslmode=require when not specified.
        if "sslmode" not in url:
            sep = "&" if "?" in url else "?"
            return psycopg2.connect(f"{url}{sep}sslmode=require")
        raise


def get_connection():
    global _working_url
    if not PSYCOPG2_AVAILABLE:
        raise RuntimeError("psycopg2 module is not installed.")
    if not settings.DATABASE_URL or "[YOUR-PASSWORD]" in settings.DATABASE_URL:
        raise ValueError("DATABASE_URL is not set or still contains placeholder password.")

    if _working_url:
        return _try_connect(_working_url)

    last_error = None
    for candidate in _repair_candidates(settings.DATABASE_URL):
        try:
            conn = _try_connect(candidate)
            if candidate != settings.DATABASE_URL:
                logger.warning("DATABASE_URL was malformed; using repaired connection string.")
            _working_url = candidate
            return conn
        except Exception as e:
            last_error = e
            continue

    raise last_error if last_error else RuntimeError("Could not connect to database.")


def init_db():
    """Create or update the blogs table and indexes if they do not exist."""
    if not settings.DATABASE_URL or "[YOUR-PASSWORD]" in settings.DATABASE_URL:
        logger.warning("DATABASE_URL is not configured properly. Skipping init_db.")
        return False

    try:
        conn = get_connection()
        with conn:
            with conn.cursor() as cur:
                # Enable pgcrypto extension if needed for gen_random_uuid.
                # Supabase may deny CREATE EXTENSION; gen_random_uuid is built-in on PG13+.
                try:
                    cur.execute("CREATE EXTENSION IF NOT EXISTS \"pgcrypto\";")
                except Exception as e:
                    logger.warning(f"Could not create pgcrypto extension (continuing): {e}")
                
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
                      AND created_at > NOW() - INTERVAL '15 minutes'
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
