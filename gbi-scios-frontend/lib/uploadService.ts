// src/lib/uploadService.ts

import { apiClient, API_BASE_URL } from "./api";
import { UploadedFile } from "@/types/upload";

export const uploadService = {
  /**
   * Uploads a single file with (very rough) progress reporting.
   *
   * NOTE: the audit flagged the previous `onProgress(10)` then `onProgress(100)`
   * as fake progress. We keep the same shape (so the UI does not need to
   * change), but use XMLHttpRequest so we get real `upload.progress` events.
   */
  uploadFileWithProgress(
    file: File,
    projectId: string,
    onProgress: (progress: number) => void,
  ): Promise<UploadedFile> {
    return new Promise((resolve, reject) => {
      const formData = new FormData();
      formData.append("file", file);
      formData.append("project_id", projectId);

      const token =
        typeof window !== "undefined" ? localStorage.getItem("access_token") : null;

      const xhr = new XMLHttpRequest();
      xhr.open("POST", `${API_BASE_URL}/uploads`);

      if (token) {
        xhr.setRequestHeader("Authorization", `Bearer ${token.trim()}`);
      }

      if (xhr.upload) {
        xhr.upload.onprogress = (event: ProgressEvent) => {
          if (event.lengthComputable) {
            const pct = Math.round((event.loaded / event.total) * 100);
            onProgress(pct);
          }
        };
      } else {
        // Fallback for browsers that don't expose upload progress.
        onProgress(10);
      }

      xhr.onload = () => {
        if (xhr.status === 401) {
          // Mirror apiClient's 401 handling.
          try {
            localStorage.removeItem("access_token");
            localStorage.removeItem("user");
            document.cookie =
              "access_token=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT; SameSite=Lax";
          } catch {
            // ignore
          }
          window.location.href = "/login";
          reject(new Error("Session expired. Please sign in again."));
          return;
        }
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const parsed = JSON.parse(xhr.responseText) as UploadedFile;
            onProgress(100);
            resolve(parsed);
          } catch {
            reject(new Error("Upload succeeded but server returned invalid JSON."));
          }
        } else {
          let message = `Upload failed (HTTP ${xhr.status})`;
          try {
            const errJson = JSON.parse(xhr.responseText);
            if (typeof errJson?.detail === "string") message = errJson.detail;
            else if (Array.isArray(errJson?.detail) && errJson.detail[0]?.msg)
              message = errJson.detail[0].msg;
          } catch {
            // ignore parse error
          }
          reject(new Error(message));
        }
      };

      xhr.onerror = () => reject(new Error("Network error during file upload."));
      xhr.send(formData);
    });
  },

  /**
   * GET /uploads/project/{projectId}?skip=&limit= → UploadedFile[].
   *
   * Audit item C-1/P-18: pass skip/limit so the backend can paginate when
   * support lands. For now, callers should be prepared to receive the full
   * list (the backend currently ignores these params).
   */
  async getFilesByProject(
    projectId: string,
    options?: { skip?: number; limit?: number },
  ): Promise<UploadedFile[]> {
    const skip = options?.skip ?? 0;
    const limit = options?.limit ?? 20;
    return apiClient.get<UploadedFile[]>(`/uploads/project/${projectId}`, {
      params: {
        skip: String(skip),
        limit: String(limit),
      },
    });
  },

  /** DELETE /uploads/{id} → 204 No Content */
  async deleteFile(id: string): Promise<void> {
    await apiClient.delete<void>(`/uploads/${id}`);
  },
};
