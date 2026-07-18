"""MinIO S3-compatible storage adapter."""

from io import BytesIO

from minio import Minio

from integrations.base import StorageAdapter


class MinioStorageAdapter(StorageAdapter):
    """Object storage via MinIO.

    Args:
        credentials: endpoint, access_key, secret_key, bucket, secure.
    """

    def __init__(self, credentials: dict) -> None:
        """Build MinIO client from credentials.

        Args:
            credentials: Connection dict.
        """
        self.bucket = credentials["bucket"]
        self.client = Minio(
            credentials["endpoint"],
            access_key=credentials["access_key"],
            secret_key=credentials["secret_key"],
            secure=credentials.get("secure", False),
        )

    def put(self, path: str, data: bytes, content_type: str) -> str:
        """Upload bytes to MinIO.

        Args:
            path: Object path.
            data: File bytes.
            content_type: MIME type.

        Returns:
            The object path.
        """
        self.client.put_object(
            self.bucket,
            path,
            BytesIO(data),
            length=len(data),
            content_type=content_type,
        )
        return path

    def get_url(self, path: str, expires_seconds: int = 3600) -> str:
        """Presigned GET URL.

        Args:
            path: Object path.
            expires_seconds: Lifetime.

        Returns:
            Presigned URL string.
        """
        from datetime import timedelta

        return self.client.presigned_get_object(
            self.bucket, path, expires=timedelta(seconds=expires_seconds)
        )
