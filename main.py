import os
from fastapi import FastAPI, HTTPException, status
from google.cloud import bigquery, storage
from datetime import datetime
import logging
from pydantic import BaseModel

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Pydantic model for the request body
class BackupRequest(BaseModel):
    dataset_id: str
    bucket_name: str

# Initialize clients   
try:
    bq_client = bigquery.Client()
    storage_client = storage.Client()
except Exception as e:
    logger.error(f"Failed to initialize Google Cloud clients: {e}")
    bq_client = None
    storage_client = None

@app.post("/backup", status_code=status.HTTP_202_ACCEPTED)
def backup_dataset(request: BackupRequest):
    """
    Triggers a backup of a BigQuery dataset to Google Cloud Storage.
    The BigQuery dataset ID and GCS bucket name are provided in the request body.
    """
    if not bq_client or not storage_client:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google Cloud clients are not initialized. Check application startup logs."
        )

    dataset_id = request.dataset_id
    bucket_name = request.bucket_name

    try:
        bucket = storage_client.get_bucket(bucket_name)
    except Exception as e:
        logger.error(f"Failed to get GCS bucket '{bucket_name}': {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"GCS bucket '{bucket_name}' not found or access denied.",
        )

    project = bq_client.project
    dataset_ref = bigquery.DatasetReference(project, dataset_id)
    
    try:
        tables = list(bq_client.list_tables(dataset_ref))
    except Exception as e:
        logger.error(f"Failed to list tables for dataset '{dataset_id}': {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"BigQuery dataset '{dataset_id}' not found or access denied.",
        )

    if not tables:
        return {"message": f"No tables found in dataset '{dataset_id}'. Nothing to back up."}

    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    backed_up_tables = []

    for table_item in tables:
        table_id = table_item.table_id
        destination_uri = f"gs://{bucket_name}/{dataset_id}/{table_id}/{timestamp}/backup-*.csv"
        table_ref = dataset_ref.table(table_id)

        extract_job_config = bigquery.ExtractJobConfig()
        extract_job_config.destination_format = bigquery.DestinationFormat.CSV

        try:
            logger.info(f"Starting backup for table '{project}.{dataset_id}.{table_id}' to '{destination_uri}'")
            extract_job = bq_client.extract_table(
                table_ref,
                destination_uri,
                job_config=extract_job_config,
                location=bq_client.get_table(table_ref).location,
            )
            logger.info(f"Successfully submitted backup job {extract_job.job_id} for table '{table_id}'")
            backed_up_tables.append(table_id)
        except Exception as e:
            logger.error(f"Failed to start backup job for table '{table_id}': {e}")
            continue
            
    if not backed_up_tables:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Backup jobs could not be started for any tables."
        )

    return {
        "message": "Backup process initiated for dataset.",
        "dataset_id": dataset_id,
        "gcs_bucket": bucket_name,
        "tables_processed": backed_up_tables,
        "info": "Backup jobs are running in the background. Check BigQuery job history for status.",
    }

@app.get("/")
def read_root():
    return {"message": "GCS Backup Service is running. POST to /backup to start a backup."} 
