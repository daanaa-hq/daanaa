"""
S3 enrichment data storage and retrieval.
Handles connection, bucket setup, and data persistence.
"""
import boto3
import logging
import os
from typing import Dict, Optional

logger = logging.getLogger(__name__)

# S3 configuration
BUCKET_NAME = 'daanaa-enrichment'
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')


def get_s3_client():
    """Get AWS S3 client. Uses AWS credentials from environment."""
    try:
        client = boto3.client('s3', region_name=AWS_REGION)
        # Test connection
        client.head_bucket(Bucket=BUCKET_NAME)
        return client
    except Exception as e:
        logger.error(f"S3 connection failed: {e}")
        logger.info("Ensure AWS credentials are configured in environment")
        return None


def ensure_bucket_exists():
    """Create S3 bucket if it doesn't exist."""
    try:
        client = boto3.client('s3', region_name=AWS_REGION)
        try:
            client.head_bucket(Bucket=BUCKET_NAME)
            logger.info(f"S3 bucket '{BUCKET_NAME}' exists")
        except client.exceptions.NoSuchBucket:
            logger.info(f"Creating S3 bucket '{BUCKET_NAME}'...")
            client.create_bucket(Bucket=BUCKET_NAME)
            logger.info(f"✓ Bucket created")

        # Set lifecycle policy: delete old versions after 90 days
        lifecycle_policy = {
            'Rules': [
                {
                    'Id': 'DeleteOldVersions',
                    'Status': 'Enabled',
                    'NoncurrentVersionExpirationInDays': 90,
                    'AbortIncompleteMultipartUpload': {'DaysAfterInitiation': 7}
                }
            ]
        }
        client.put_bucket_lifecycle_configuration(
            Bucket=BUCKET_NAME,
            LifecycleConfiguration=lifecycle_policy
        )
        logger.info(f"✓ Lifecycle policy set")

    except Exception as e:
        logger.error(f"Bucket setup failed: {e}")
        raise


def upload_contact_data(ein: str, contact: Dict) -> bool:
    """Upload contact enrichment to S3."""
    client = get_s3_client()
    if not client:
        return False

    try:
        import json
        from datetime import datetime

        s3_path = f'contact/{ein}.json'
        client.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_path,
            Body=json.dumps(contact, default=str),
            ContentType='application/json',
            Metadata={'last_updated': datetime.now().isoformat()}
        )
        logger.debug(f"✓ Uploaded {s3_path}")
        return True
    except Exception as e:
        logger.error(f"Upload failed for contact/{ein}.json: {e}")
        return False


def upload_programs_data(ein: str, programs: Dict) -> bool:
    """Upload programs enrichment to S3."""
    client = get_s3_client()
    if not client:
        return False

    try:
        import json
        from datetime import datetime

        s3_path = f'programs/{ein}.json'
        client.put_object(
            Bucket=BUCKET_NAME,
            Key=s3_path,
            Body=json.dumps(programs, default=str),
            ContentType='application/json',
            Metadata={'last_updated': datetime.now().isoformat()}
        )
        logger.debug(f"✓ Uploaded {s3_path}")
        return True
    except Exception as e:
        logger.error(f"Upload failed for programs/{ein}.json: {e}")
        return False


def get_contact_data(ein: str) -> Optional[Dict]:
    """Retrieve contact enrichment from S3."""
    client = get_s3_client()
    if not client:
        return None

    try:
        import json
        response = client.get_object(Bucket=BUCKET_NAME, Key=f'contact/{ein}.json')
        return json.loads(response['Body'].read())
    except client.exceptions.NoSuchKey:
        return None
    except Exception as e:
        logger.warning(f"Retrieval failed for contact/{ein}.json: {e}")
        return None


def get_programs_data(ein: str) -> Optional[Dict]:
    """Retrieve programs enrichment from S3."""
    client = get_s3_client()
    if not client:
        return None

    try:
        import json
        response = client.get_object(Bucket=BUCKET_NAME, Key=f'programs/{ein}.json')
        return json.loads(response['Body'].read())
    except client.exceptions.NoSuchKey:
        return None
    except Exception as e:
        logger.warning(f"Retrieval failed for programs/{ein}.json: {e}")
        return None


def list_enriched_orgs(prefix: str = '') -> list:
    """List all EINs with enrichment data in S3."""
    client = get_s3_client()
    if not client:
        return []

    try:
        eins = set()
        paginator = client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=BUCKET_NAME, Prefix=prefix)

        for page in pages:
            if 'Contents' not in page:
                continue
            for obj in page['Contents']:
                # Extract EIN from key like 'contact/123456789.json'
                parts = obj['Key'].split('/')
                if len(parts) == 2:
                    ein = parts[1].replace('.json', '')
                    eins.add(ein)

        return sorted(list(eins))
    except Exception as e:
        logger.error(f"List failed: {e}")
        return []


def get_bucket_stats() -> Dict:
    """Get S3 bucket storage stats."""
    client = get_s3_client()
    if not client:
        return {}

    try:
        response = client.list_objects_v2(Bucket=BUCKET_NAME)
        total_size = sum(obj.get('Size', 0) for obj in response.get('Contents', []))
        total_objects = response.get('KeyCount', 0)

        return {
            'bucket': BUCKET_NAME,
            'objects': total_objects,
            'size_bytes': total_size,
            'size_mb': round(total_size / (1024 ** 2), 2),
            'estimated_monthly_cost': round(total_size / (1024 ** 3) * 0.023, 2)  # $0.023/GB
        }
    except Exception as e:
        logger.error(f"Stats failed: {e}")
        return {}
