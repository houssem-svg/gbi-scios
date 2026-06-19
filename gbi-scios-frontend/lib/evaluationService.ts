/**
 * Service layer for the bid evaluation engine.
 *
 * Wraps apiClient calls to /api/v1/evaluations/* and returns typed responses.
 * All endpoints require authentication (apiClient injects the Bearer token).
 */

import { apiClient } from "./api";
import type {
  Bid,
  BidCreateInput,
  CriteriaUpdateInput,
  EvaluationCriteria,
  EvaluationRunResponse,
} from "@/types/evaluation";

export const evaluationService = {
  /** GET /evaluations/criteria/{projectId} — get-or-create the project's criteria. */
  async getCriteria(projectId: string): Promise<EvaluationCriteria> {
    return apiClient.get<EvaluationCriteria>(
      `/evaluations/criteria/${projectId}`,
    );
  },

  /** PUT /evaluations/criteria/{projectId} — update editable criteria fields. */
  async updateCriteria(
    projectId: string,
    data: CriteriaUpdateInput,
  ): Promise<EvaluationCriteria> {
    return apiClient.put<EvaluationCriteria>(
      `/evaluations/criteria/${projectId}`,
      data,
    );
  },

  /** POST /evaluations/bids/{projectId} — create a new bid for the project. */
  async createBid(
    projectId: string,
    data: BidCreateInput,
  ): Promise<Bid> {
    return apiClient.post<Bid>(`/evaluations/bids/${projectId}`, data);
  },

  /** GET /evaluations/bids/{projectId} — list all bids for the project. */
  async listBids(projectId: string): Promise<Bid[]> {
    const res = await apiClient.get<Bid[]>(`/evaluations/bids/${projectId}`);
    return Array.isArray(res) ? res : [];
  },

  /** POST /evaluations/run/{projectId} — run the evaluation engine. */
  async runEvaluation(projectId: string): Promise<EvaluationRunResponse> {
    return apiClient.post<EvaluationRunResponse>(
      `/evaluations/run/${projectId}`,
      {},
    );
  },
};
