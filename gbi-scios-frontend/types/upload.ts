// src/types/upload.ts

export interface UploadedFile {
  id: string;
  filename: string;
  file_size: number;
  content_type: string;
  project_id: string;
  created_at: string;
}

export const ALLOWED_FILE_TYPES = [
  "text/csv",
  "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
  "application/pdf",
];

export const MAX_FILE_SIZE = 50 * 1024 * 1024; // 50MB