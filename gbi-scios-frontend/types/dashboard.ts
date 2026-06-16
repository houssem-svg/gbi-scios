// src/types/dashboard.ts

export interface Alert {
  id: string;
  severity: 'Critical' | 'High' | 'Medium' | 'Low';
  message: string;
  timestamp: string;
}

export interface TrendPoint {
  date: string;
  exposure: number;
}

export interface DashboardSummary {
  total_exposure: number;
  exposure_change: number;
  compliance_score: number;
  compliance_change: number;
  active_projects: number;
  critical_risks: number;
  alerts: Alert[];
  exposure_trends: TrendPoint[];
}