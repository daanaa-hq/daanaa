"""
Generate org embeddings for semantic search via GPU embedding server.
Runs in parallel with contact/programs extraction (Layer 2).
Stores embeddings to S3 for similarity search features.
"""
import requests
import json
import logging
from typing import Optional, List

logger = logging.getLogger(__name__)

EMBED_SERVER_URL = "http://127.0.0.1:11434/embedding"
EMBED_TIMEOUT = 30


def generate_org_embedding(org: dict) -> Optional[List[float]]:
    """
    Generate semantic embedding for an org using mxbai-embed-large.
    Embeds: org name + mission (text representation for similarity search).
    Returns: 384-dim vector, or None if failed.
    """
    try:
        # Build text representation: org name + mission (most semantic)
        org_name = org.get('organization_name', '').strip()
        mission = org.get('mission', '').strip()

        if not org_name:
            return None

        # Combine fields for embedding
        text = f"{org_name}. {mission}" if mission else org_name
        text = text[:1024]  # Truncate to reasonable length

        # Call embedding server
        response = requests.post(
            EMBED_SERVER_URL,
            json={"content": text},
            timeout=EMBED_TIMEOUT
        )

        if response.status_code == 200:
            data = response.json()
            embedding = data.get('embedding')
            if embedding and isinstance(embedding, list) and len(embedding) > 0:
                logger.debug(f"Embedding generated for {org['EIN']}: {len(embedding)} dims")
                return embedding
        else:
            logger.warning(f"Embedding server returned {response.status_code}")

    except requests.exceptions.Timeout:
        logger.warning(f"Embedding timeout for {org['EIN']}")
    except requests.exceptions.ConnectionError:
        logger.warning(f"Embedding server unavailable (port 11436)")
    except Exception as e:
        logger.warning(f"Embedding generation failed for {org['EIN']}: {e}")

    return None


def upload_embedding(ein: str, embedding: List[float]) -> bool:
    """Upload embedding to S3 enrichment storage."""
    try:
        from scripts.s3_enrichment import upload_embedding_data
        return upload_embedding_data(ein, {"embedding": embedding, "dims": len(embedding)})
    except Exception as e:
        logger.warning(f"Failed to upload embedding for {ein}: {e}")
        return False
