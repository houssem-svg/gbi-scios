// src/lib/uploadService.ts

import { apiClient } from "./api";
import { UploadedFile } from "@/types/upload";

const BASE_URL = "http://127.0.0.1:8000/api/v1";

export const uploadService = {
  async getFilesByProject(projectId: string): Promise<UploadedFile[]> {
    return apiClient.get<UploadedFile[]>(`/uploads/project/${projectId}`);
  },

  async deleteFile(id: string): Promise<void> {
    return apiClient.delete<void>(`/uploads/${id}`);
  },

  uploadFileWithProgress(
    file: File,
    projectId: string,
    onProgress: (progress: number) => void
  ): Promise<UploadedFile> {
    return new Promise((resolve, reject) => {
      const xhr = new XMLHttpRequest();
      const formData = new FormData();
      formData.append("file", file);
      formData.append("project_id", projectId);

      xhr.upload.addEventListener("progress", (event) => {
        if (event.lengthComputable) {
          const percentComplete = Math.round((event.loaded / event.total) * 100);
          onProgress(percentComplete);
        }
      });

      xhr.addEventListener("load", () => {
        if (xhr.status >= 200 && xhr.status < 300) {
          try {
            const response = JSON.parse(xhr.responseText);
            resolve(response);
          } catch (e) {
            resolve({} as UploadedFile);
          }
        } else {
          let errorMessage = "Upload failed";
          try {
            const errorResponse = JSON.parse(xhr.responseText);
            errorMessage =
              typeof errorResponse.detail === "string"
                ? errorResponse.detail
                : errorResponse.detail?.[0]?.msg || errorMessage;
          } catch (e) {}
          reject(new Error(errorMessage));
        }
      });

      xhr.addEventListener("error", () => reject(new Error("Network Error")));
      xhr.addEventListener("abort", () => reject(new Error("Upload Aborted")));

      const cleanEndpoint = "/uploads";
      xhr.open("POST", `${BASE_URL}${cleanEndpoint}`);

      const token = localStorage.getItem("access_token");
      if (token) {
        xhr.setRequestHeader("Authorization", `Bearer ${token.trim()}`);
      }

      // Do NOT set Content-Type; the browser automatically sets it with the multipart boundary
      xhr.send(formData);
    });
  },
};
