"""
Upload Service for MRPC Forum Data
Handles CSV file uploads with authentication and validation
"""

import pandas as pd
import io
import base64
from typing import Dict, List, Tuple
from .mrpc_database import MRPCDatabase
from .auth import get_current_user_id


class UploadService:
    """Service class for handling CSV uploads with authentication"""

    def __init__(self):
        self.db = MRPCDatabase()

    def validate_csv_structure(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate that CSV has required columns and structure

        Args:
            df (pd.DataFrame): DataFrame to validate

        Returns:
            Tuple[bool, List[str]]: (is_valid, list_of_errors)
        """
        errors = []

        # Required columns for forum data (id column is always missing and will be auto-generated)
        # Note: llm_cluster_name, date_posted may also be missing and will be set to None
        required_columns = ["forum", "original_title", "original_post"]

        # Optional but expected columns (will be mapped if present with different names)
        expected_mappings = {
            "LLM_inferred_question": "LLM_inferred_question",  # Keep original name
            "umap_x": "umap_1",
            "umap_y": "umap_2",
            "umap_z": "umap_3",
        }

        # Check for required columns
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            errors.append(f"Missing required columns: {', '.join(missing_columns)}")

        # Check if expected columns are present (with mappings)
        has_inference_question = any(
            col in df.columns
            for col in ["LLM_inferred_question", "llm_inferred_question"]
        )
        has_umap_coords = all(
            col in df.columns for col in ["umap_x", "umap_y", "umap_z"]
        ) or all(col in df.columns for col in ["umap_1", "umap_2", "umap_3"])

        if not has_inference_question:
            errors.append(
                "Missing LLM inferred question column (expected 'LLM_inferred_question' or 'llm_inferred_question')"
            )

        if not has_umap_coords:
            errors.append(
                "Missing UMAP coordinates (expected 'umap_x,umap_y,umap_z' or 'umap_1,umap_2,umap_3')"
            )

        # Check for empty DataFrame
        if len(df) == 0:
            errors.append("CSV file is empty")

        # Note: No duplicate ID check since id column is always missing from CSV files
        # Duplicate detection is handled via composite key (original_title + llm_inferred_question)

        return len(errors) == 0, errors

    def detect_upload_type(self, df: pd.DataFrame) -> str:
        """
        Detect whether upload is forum data or transcription data based on CSV columns

        Args:
            df (pd.DataFrame): DataFrame to analyze

        Returns:
            str: 'forum_data' or 'transcription_data'
        """
        # Transcription-specific columns that strongly indicate transcription data
        transcription_indicators = [
            "session_id",
            "participant_id",
            "zoom_ease",
            "poll_usability",
            "presession_anxiety",
            "reassurance_provided",
            "info_useful",
            "exercise_engaged",
            "lifestyle_change",
            "family_involved",
        ]

        # Forum-specific columns that strongly indicate forum data
        forum_indicators = [
            "forum",
            "original_title",
            "original_post",
            "cluster",
            "llm_inferred_question",
            "LLM_inferred_question",
            "umap_1",
            "umap_x",
        ]

        # Handle empty dataframes
        if df.empty:
            return "unknown"

        # Count how many indicator columns are present
        transcription_score = sum(
            1 for col in transcription_indicators if col in df.columns
        )
        forum_score = sum(1 for col in forum_indicators if col in df.columns)

        # Decision logic: transcription data needs multiple transcription indicators
        # and minimal forum indicators
        if transcription_score >= 3 and forum_score <= 1:
            return "transcription_data"
        elif forum_score >= 2:
            return "forum_data"
        else:
            # Default to forum_data if unclear (backward compatibility)
            return "forum_data"

    def validate_transcription_csv(self, df: pd.DataFrame) -> Tuple[bool, List[str]]:
        """
        Validate transcription CSV structure with strict requirements

        Args:
            df (pd.DataFrame): DataFrame to validate

        Returns:
            Tuple[bool, List[str]]: (is_valid, list_of_errors)
        """
        errors = []

        # ALL columns are required for transcription data
        required_columns = [
            "session_id",
            "participant_id",
            "zoom_ease",
            "poll_usability",
            "resource_access",
            "presession_anxiety",
            "reassurance_provided",
            "info_useful",
            "info_missing",
            "info_takeaway_desired",
            "exercise_engaged",
            "lifestyle_change",
            "postop_adherence",
            "family_involved",
            "support_needed",
        ]

        # Check ALL required columns are present
        missing_required = [col for col in required_columns if col not in df.columns]
        if missing_required:
            errors.append(f"Missing required columns: {', '.join(missing_required)}")

        # Validate ALL Likert scale columns (1-5)
        likert_columns = [
            "poll_usability",
            "presession_anxiety",
            "reassurance_provided",
            "info_useful",
        ]

        for likert_col in likert_columns:
            if likert_col in df.columns:
                # Check for valid Likert values (1-5), excluding NaN values
                valid_mask = df[likert_col].notna() & df[likert_col].between(1, 5)
                invalid_values = len(df[~valid_mask & df[likert_col].notna()])
                if invalid_values > 0:
                    errors.append(
                        f"{likert_col} must be 1-5 (found {invalid_values} invalid values)"
                    )

        # Validate Boolean columns
        boolean_columns = [
            "zoom_ease",
            "resource_access",
            "info_missing",
            "info_takeaway_desired",
            "exercise_engaged",
            "lifestyle_change",
            "postop_adherence",
            "family_involved",
            "support_needed",
        ]

        for bool_col in boolean_columns:
            if bool_col in df.columns:
                # Check for valid boolean representations
                invalid_bools = 0
                for val in df[bool_col].dropna():
                    if not self._is_valid_boolean_value(val):
                        invalid_bools += 1

                if invalid_bools > 0:
                    errors.append(
                        f"{bool_col} must be True/False/Yes/No/1/0 (found {invalid_bools} invalid values)"
                    )

        # Check for empty DataFrame
        if len(df) == 0:
            errors.append("CSV file is empty")

        return len(errors) == 0, errors

    def _is_valid_boolean_value(self, value) -> bool:
        """Check if value can be converted to boolean"""
        if isinstance(value, bool):
            return True
        if isinstance(value, (int, float)):
            return value in [0, 1]
        if isinstance(value, str):
            lower_val = value.lower().strip()
            return lower_val in ["true", "false", "yes", "no", "1", "0", "y", "n"]
        return False

    def _parse_csv_contents(self, contents: str) -> pd.DataFrame:
        """
        Parse CSV contents from base64 encoded string

        Args:
            contents (str): Base64 encoded file contents

        Returns:
            pd.DataFrame: Parsed CSV data
        """
        content_type, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)
        return pd.read_csv(io.StringIO(decoded.decode("utf-8")))

    def process_file_upload(
        self,
        contents: str,
        filename: str,
        user_readable_name: str,
        comment: str = None,
        expected_type: str = None,
    ) -> Dict:
        """
        Process an uploaded CSV file

        Args:
            contents (str): Base64 encoded file contents
            filename (str): Original filename
            user_readable_name (str): Human-readable name for the upload
            comment (str, optional): User comment about the upload
            expected_type (str, optional): Expected upload type ('forum_data' or 'transcription_data')

        Returns:
            Dict: Result with success status, message, and optional upload_id
        """
        try:
            # Get current user
            user_id = get_current_user_id()
            if not user_id:
                return {
                    "success": False,
                    "message": "Authentication required to upload files",
                }

            # Decode file contents
            content_type, content_string = contents.split(",")
            decoded = base64.b64decode(content_string)

            # Read CSV data
            try:
                df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
            except Exception as e:
                return {
                    "success": False,
                    "message": f"Error reading CSV file: {str(e)}",
                }

            # Determine upload type - use expected_type if provided, otherwise auto-detect
            if expected_type:
                upload_type = expected_type
                # Verify the expected type matches the data
                detected_type = self.detect_upload_type(df)
                if detected_type != expected_type:
                    return {
                        "success": False,
                        "message": f"Data type mismatch: Selected '{expected_type.replace('_', ' ').title()}' but data appears to be '{detected_type.replace('_', ' ').title()}'. Please check your file or change the data type selection.",
                    }
            else:
                # Fallback to auto-detection for backward compatibility
                upload_type = self.detect_upload_type(df)

            # Validate CSV structure based on determined type
            if upload_type == "transcription_data":
                is_valid, errors = self.validate_transcription_csv(df)
            else:
                is_valid, errors = self.validate_csv_structure(df)

            if not is_valid:
                error_details = []
                if upload_type == "transcription_data":
                    error_details.append("❌ Transcription Data Validation Failed")
                    error_details.append(
                        "Required: ALL 15 experimental fields must be present and properly formatted"
                    )
                    error_details.append("Validation Errors:")
                    error_details.extend([f"  • {error}" for error in errors])
                    error_details.append(
                        "\nTip: Check the Data Type Selection guide above for field requirements"
                    )
                else:
                    error_details.append("❌ Forum Data Validation Failed")
                    error_details.extend([f"  • {error}" for error in errors])

                return {
                    "success": False,
                    "message": "\n".join(error_details),
                }

            # Create upload record with determined type
            upload_id = self.db.create_upload_record(
                filename=filename,
                user_readable_name=user_readable_name,
                uploaded_by=user_id,
                comment=comment,
                upload_type=upload_type,
            )

            # Process the data based on upload type
            if upload_type == "transcription_data":
                upload_result = self.db.save_transcription_data(df, upload_id)
            else:
                upload_result = self.db.upload_csv_data(upload_id, df, user_id)

            if upload_result["success"]:
                if upload_type == "transcription_data":
                    return {
                        "success": True,
                        "message": upload_result["message"],
                        "upload_id": upload_id,
                        "upload_type": upload_type,
                        "records_saved": upload_result.get("records_saved", 0),
                    }
                else:
                    return {
                        "success": True,
                        "message": upload_result["message"],
                        "upload_id": upload_id,
                        "upload_type": upload_type,
                        "new_records": upload_result["new_records"],
                        "duplicates_skipped": upload_result["duplicates_skipped"],
                        "total_processed": upload_result["total_processed"],
                    }
            else:
                return {
                    "success": False,
                    "message": upload_result["message"],
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"Unexpected error during upload: {str(e)}",
            }

    def get_user_uploads(
        self, status: str = None, upload_type: str = None
    ) -> List[Dict]:
        """
        Get uploads for the current authenticated user, optionally filtered by status and type

        Args:
            status (str, optional): Filter by status ('active', 'archived', 'deleted')
            upload_type (str, optional): Filter by upload type ('forum_data', 'transcription_data')

        Returns:
            List[Dict]: List of upload records for current user
        """
        user_id = get_current_user_id()
        if not user_id:
            return []

        return self.db.get_all_uploads(
            user_id=user_id, status=status, upload_type=upload_type
        )

    def get_all_uploads(self, status: str = None) -> List[Dict]:
        """
        Get all uploads (admin function), optionally filtered by status

        Args:
            status (str, optional): Filter by status ('active', 'archived', 'deleted')

        Returns:
            List[Dict]: List of all upload records
        """
        return self.db.get_all_uploads(status=status)

    def archive_upload(self, upload_id: int) -> Dict:
        """
        Archive an upload (user can only archive their own active uploads)

        Args:
            upload_id (int): Upload ID to archive

        Returns:
            Dict: Result with success status and message
        """
        try:
            user_id = get_current_user_id()
            if not user_id:
                return {
                    "success": False,
                    "message": "Authentication required to archive uploads",
                }

            result = self.db.archive_upload(upload_id, user_id=user_id)

            if result["success"]:
                return {
                    "success": True,
                    "message": f"Successfully archived upload '{result['upload_name']}' with {result['records_count']} records",
                    "upload_name": result["upload_name"],
                    "records_count": result["records_count"],
                }
            else:
                return {
                    "success": False,
                    "message": result["message"],
                }

        except Exception as e:
            return {"success": False, "message": f"Error archiving upload: {str(e)}"}

    def restore_upload(self, upload_id: int) -> Dict:
        """
        Restore an archived upload (user can only restore their own uploads)

        Args:
            upload_id (int): Upload ID to restore

        Returns:
            Dict: Result with success status and message
        """
        try:
            user_id = get_current_user_id()
            if not user_id:
                return {
                    "success": False,
                    "message": "Authentication required to restore uploads",
                }

            result = self.db.restore_upload(upload_id, user_id=user_id)

            if result["success"]:
                return {
                    "success": True,
                    "message": f"Successfully restored upload '{result['upload_name']}' with {result['records_count']} records",
                    "upload_name": result["upload_name"],
                    "records_count": result["records_count"],
                }
            else:
                return {
                    "success": False,
                    "message": result["message"],
                }

        except Exception as e:
            return {"success": False, "message": f"Error restoring upload: {str(e)}"}

    def delete_upload(self, upload_id: int) -> Dict:
        """
        Delete an upload (ONLY archived uploads, user can only delete their own)

        Args:
            upload_id (int): Upload ID to delete

        Returns:
            Dict: Result with success status and message
        """
        try:
            user_id = get_current_user_id()
            if not user_id:
                return {
                    "success": False,
                    "message": "Authentication required to delete uploads",
                }

            result = self.db.delete_upload_soft(upload_id, user_id=user_id)

            if result["success"]:
                return {
                    "success": True,
                    "message": f"Successfully deleted upload '{result['upload_name']}' with {result['records_count']} records",
                    "upload_name": result["upload_name"],
                    "records_count": result["records_count"],
                }
            else:
                return {
                    "success": False,
                    "message": result["message"],
                }

        except Exception as e:
            return {"success": False, "message": f"Error deleting upload: {str(e)}"}

    def delete_upload_permanent(self, upload_id: int) -> Dict:
        """
        Permanently delete an upload (ADMIN ONLY, only deleted uploads)

        Args:
            upload_id (int): Upload ID to permanently delete

        Returns:
            Dict: Result with success status and message
        """
        try:
            user_id = get_current_user_id()
            if not user_id:
                return {
                    "success": False,
                    "message": "Authentication required to permanently delete uploads",
                }

            result = self.db.delete_upload_permanent(upload_id, user_id=user_id)

            if result["success"]:
                return {
                    "success": True,
                    "message": f"Permanently deleted upload '{result['upload_name']}' and all associated data",
                    "upload_name": result["upload_name"],
                    "records_deleted": result["records_deleted"],
                }
            else:
                return {
                    "success": False,
                    "message": result["message"],
                }

        except Exception as e:
            return {
                "success": False,
                "message": f"Error permanently deleting upload: {str(e)}",
            }

    def delete_upload_old(self, upload_id: int) -> Dict:
        """
        DEPRECATED: Delete an upload and its data (user can only delete their own uploads)
        Use archive_upload(), delete_upload(), or delete_upload_permanent() instead

        Args:
            upload_id (int): Upload ID to delete

        Returns:
            Dict: Result with success status and message
        """
        try:
            user_id = get_current_user_id()
            if not user_id:
                return {
                    "success": False,
                    "message": "Authentication required to delete uploads",
                }

            success = self.db.delete_upload_and_data(upload_id, user_id=user_id)

            if success:
                return {
                    "success": True,
                    "message": f"Successfully deleted upload {upload_id} and associated data",
                }
            else:
                return {
                    "success": False,
                    "message": "Failed to delete upload (not found or not authorized)",
                }

        except Exception as e:
            return {"success": False, "message": f"Error deleting upload: {str(e)}"}

    def get_upload_statistics(self) -> Dict:
        """
        Get upload statistics

        Returns:
            Dict: Upload statistics
        """
        return self.db.get_upload_statistics()

    def preview_csv(self, contents: str, rows: int = 5) -> Dict:
        """
        Preview first few rows of uploaded CSV without saving

        Args:
            contents (str): Base64 encoded file contents
            rows (int): Number of rows to preview

        Returns:
            Dict: Preview data and validation results
        """
        try:
            # Decode file contents
            content_type, content_string = contents.split(",")
            decoded = base64.b64decode(content_string)

            # Read CSV data
            try:
                df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
            except Exception as e:
                return {
                    "success": False,
                    "message": f"Error reading CSV file: {str(e)}",
                }

            # Validate structure
            is_valid, errors = self.validate_csv_structure(df)

            # Get preview data
            preview_df = df.head(rows)

            return {
                "success": True,
                "total_rows": len(df),
                "columns": list(df.columns),
                "preview_data": preview_df.to_dict("records"),
                "is_valid": is_valid,
                "validation_errors": errors if not is_valid else [],
            }

        except Exception as e:
            return {"success": False, "message": f"Error previewing CSV: {str(e)}"}


# Global instance for use in callbacks
upload_service = UploadService()
