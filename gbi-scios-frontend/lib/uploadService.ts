// src/lib/uploadService.ts

export const uploadService = {
  uploadFileWithProgress: async (
    file: File, 
    projectId: string, 
    onProgress: (progress: number) => void
  ): Promise<any> => {
    
    const formData = new FormData();
    formData.append("file", file);
    formData.append("project_id", projectId);

    onProgress(10);

    // 🚨 استخراج مفتاح الدخول (Token) من المتصفح
    const token = typeof window !== "undefined" ? localStorage.getItem("access_token") : null;
    
    const headers: Record<string, string> = {};
    if (token) {
      // 🚨 إضافة المفتاح السري للطلب لكي يقبله خادم FastAPI
      headers["Authorization"] = `Bearer ${token.trim()}`;
    }

    const response = await fetch("http://localhost:8000/api/v1/uploads", {
      method: "POST",
      headers: headers, // أضفنا الهيدر هنا
      body: formData,
    });

    onProgress(100);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      console.error("Upload Error:", errorData);
      throw new Error("Failed to upload file");
    }

    return response.json();
  }
};