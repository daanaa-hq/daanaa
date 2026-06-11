import os

# Importing daanaa_api eagerly loads ~546K org embeddings (2+ GB). Tests never
# need the vector matrix — skip the load before any test module imports the API.
os.environ.setdefault("DAANAA_SKIP_EMBEDDINGS", "1")
