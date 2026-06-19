// src/types/upload.ts

/**
 * Mirrors backend `UploadedFileRead` (app/schemas/upload.py):
 * { id, project_id, original_filename, storage_path, file_type, uploaded_by, uploaded_at }
 *
 * NOTE: file_type is the backend `uploaded_file_type` enum (e.g. "boq",
 * "mandatory_list", "compliance_evidence", "other"). We type it loosely as a
 * string here so the frontend tolerates enum additions without breaking.
 */
export interface UploadedFile {
  id: string;
  project_id: string;
  original_filename: string;
  storage_path: string;
  file_type: string;
  uploaded_by: string;
  uploaded_at: string;
}

export const ALLOWED_FILE_TYPES = [
  "text/csv",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  "application/vnd.ms-excel",
  "application/pdf",
];

export const ALLOWED_FILE_EXTENSIONS = [".csv", ".xlsx", ".xls", ".pdf"];

export const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB
