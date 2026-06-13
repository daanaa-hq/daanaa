import os, tempfile

# Skip the ~2GB embedding load — tests never need the vector matrix.
os.environ.setdefault("DAANAA_SKIP_EMBEDDINGS", "1")

# Use a temp file DB so tests never touch the live DB (and work even when it's locked).
_tmp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
_tmp_db.close()
os.environ.setdefault("DB_PATH", _tmp_db.name)
os.environ.setdefault("LIVE_DB_PATH", _tmp_db.name)
