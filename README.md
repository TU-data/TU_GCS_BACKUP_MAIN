# GCS BigQuery 백업 서비스 (Cloud Scheduler 연동 가이드)

이 서비스는 Google Cloud BigQuery 데이터셋을 Google Cloud Storage(GCS) 버킷으로 백업하는 기능을 제공합니다. Cloud Scheduler를 사용하여 정기적으로 백업을 자동화할 수 있습니다.

## 1. 사전 준비 사항

서비스를 사용하기 전에 다음 Google Cloud 리소스가 준비되어 있어야 합니다.

*   **BigQuery 데이터셋**: 백업할 대상 BigQuery 데이터셋이 존재해야 합니다.
*   **GCS 버킷**: 백업된 파일이 저장될 GCS 버킷이 존재해야 합니다.
*   **Cloud Run 서비스 계정 권한**:
    *   Cloud Run 서비스가 사용하는 서비스 계정 (일반적으로 `PROJECT_NUMBER-compute@developer.gserviceaccount.com`)에 다음 역할이 부여되어야 합니다:
        *   **BigQuery 데이터셋**: `BigQuery 데이터 뷰어` (roles/bigquery.dataViewer)
        *   **GCS 버킷**: `Storage 개체 생성자` (roles/storage.objectCreator) 및 `Storage 개체 뷰어` (roles/storage.objectViewer)

## 2. 서비스 배포 (개발자용)

이 서비스는 Google Cloud Run에 배포되어야 합니다. 일반적으로 `cloudbuild.yaml` 파일을 통해 Cloud Build 파이프라인을 설정하여 Git 저장소에 코드가 푸시될 때 자동으로 빌드 및 배포되도록 구성할 수 있습니다.

**참고**: 코드를 변경한 후에는 반드시 Cloud Build를 통해 새로운 이미지를 빌드하고 Cloud Run 서비스에 배포해야 변경사항이 적용됩니다.

## 3. Cloud Scheduler 작업 설정

BigQuery 데이터셋 백업을 자동화하기 위해 Cloud Scheduler 작업을 설정합니다.

1.  Google Cloud Console에서 **Cloud Scheduler**로 이동합니다.
2.  **작업 만들기**를 클릭합니다.
3.  다음과 같이 작업 세부 정보를 구성합니다:
    *   **이름**: 작업의 고유한 이름을 지정합니다 (예: `backup-my-dataset-daily`).
    *   **리전**: Cloud Run 서비스가 배포된 리전과 동일하게 설정합니다 (예: `asia-northeast3`).
    *   **빈도**: Cron 표현식을 사용하여 백업을 실행할 주기를 설정합니다 (예: 매일 자정 실행 `0 0 * * *`).
    *   **시간대**: `Asia/Seoul` (한국 시간)로 설정합니다.

4.  **실행 구성** 섹션에서 다음을 설정합니다:
    *   **대상**: `HTTP`
    *   **URL**: 배포된 Cloud Run 서비스의 `/backup` 엔드포인트 URL을 입력합니다.
        *   예시: `https://gcs-backup-service-xxxxxxxxxx.asia-northeast3.run.app/backup`
        *   `xxxxxxxxxx` 부분은 실제 Cloud Run 서비스 URL에 따라 달라집니다.

    *   **HTTP 메서드**:
        *   **POST (권장)**: 요청 본문에 `dataset_id`와 `bucket_name`을 JSON 형식으로 포함합니다.
            ```json
            {
              "dataset_id": "your_bigquery_dataset_id",
              "bucket_name": "your_gcs_bucket_name"
            }
            ```
        *   **GET**: 쿼리 파라미터로 `dataset_id`와 `bucket_name`을 포함합니다.
            ```
            https://gcs-backup-service-xxxxxxxxxx.asia-northeast3.run.app/backup?dataset_id=your_bigquery_dataset_id&bucket_name=your_gcs_bucket_name
            ```
            **참고**: `GET` 메서드 사용 시 URL 인코딩에 유의해야 합니다.

    *   **인증**:
        *   만약 Cloud Run 서비스가 `allow-unauthenticated`로 배포되었다면, **인증 헤더 추가**를 `없음`으로 설정합니다.
        *   만약 인증이 필요하다면, `OIDC 토큰`을 선택하고 서비스 계정을 지정해야 합니다.

5.  **만들기**를 클릭하여 작업을 저장합니다.

## 4. 백업 파일 형식 및 이름

*   **파일 형식**: 백업된 파일은 **PARQUET** 형식으로 GCS 버킷에 저장됩니다.
*   **파일 이름**: 백업 파일은 다음 형식으로 생성됩니다:
    `gs://<버킷_이름>/<데이터셋_ID>/<테이블_ID>/<테이블_ID>_<한국시간_타임스탬프>_*.parquet`
    *   `<한국시간_타임스탬프>`는 백업이 시작된 한국 시간 (KST, UTC+9)을 `YYYYMMDDHHMMSS` 형식으로 나타냅니다.

## 5. 모니터링 및 문제 해결

*   **Cloud Scheduler 로그**: Cloud Scheduler 작업의 실행 성공/실패 여부를 확인합니다. 실패 시 오류 메시지를 통해 초기 문제를 파악할 수 있습니다.
*   **Cloud Run 로그**: Cloud Run 서비스의 로그를 확인하여 백업 프로세스의 상세 로그 및 발생한 오류를 확인할 수 있습니다. BigQuery 또는 GCS 관련 오류 메시지가 여기에 표시됩니다.
*   **GCS 버킷**: 백업 작업이 완료된 후 지정된 GCS 버킷에 백업 파일이 올바르게 생성되었는지 확인합니다. 파일 형식과 이름이 예상과 일치하는지 확인합니다.
*   **BigQuery 작업 기록**: BigQuery 콘솔에서 작업 기록을 확인하여 데이터 내보내기 작업의 성공 여부 및 상세 정보를 확인할 수 있습니다.
