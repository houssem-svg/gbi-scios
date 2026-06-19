// gbi-scios-frontend/lib/uploadService.ts

import { apiClient, API_BASE_URL } from "./api";
import { UploadedFile } from "@/types/upload";

export const uploadService = {
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
        onProgress(10);
      }

      xhr.onload = () => {
        if (xhr.status === 401) {
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

  async deleteFile(id: string): Promise<void> {
    await apiClient.delete<void>(`/uploads/${id}`);
  },
};
