// src/lib/parsingService.ts

import { apiClient } from "./api";

export interface BoQItem {
  id: string;
  project_id: string;
  item_code: string;
  description: string;
  quantity: number;
  unit_price: number;
  total_price: number;
  sourcing_type: string;
  created_at: string;
}

export interface BoQParseResult {
  parsed_rows: number;
  failed_rows: number;
  validation_errors: string[];
  items: BoQItem[];
}

export const parsingService = {
  /** POST /parsing/boq/{uploadedFileId} — parse an uploaded BoQ file. */
  async parseBoq(uploadedFileId: string): Promise<BoQParseResult> {
    return apiClient.post<BoQParseResult>(
      `/parsing/boq/${uploadedFileId}`,
      {},
    );
  },

  /** GET /parsing/boq/project/{projectId} — list parsed BoQ items. */
  async listBoqItems(
    projectId: string,
    options?: { skip?: number; limit?: number },
  ): Promise<BoQItem[]> {
    const skip = options?.skip ?? 0;
    const limit = options?.limit ?? 200;
    const res = await apiClient.get<BoQItem[]>(
      `/parsing/boq/project/${projectId}`,
      { params: { skip: String(skip), limit: String(limit) } },
    );
    return Array.isArray(res) ? res : [];
  },
};
