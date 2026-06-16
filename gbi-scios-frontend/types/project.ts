// types/project.ts

export interface Project {
  id: string;
  // الحقول الأصلية (للواجهة الأمامية)
  name: string;
  client: string;
  compliance_score: number;
  risk_level: 'Low' | 'Moderate' | 'High' | 'Critical';
  status: 'Active' | 'Review' | 'Compliant' | 'Planning';
  created_at: string;

  // الحقول الإضافية (لتتوافق مع الباكيند الجديد FastAPI دون أخطاء)
  project_name?: string;
  client_name?: string;
  sector?: string;
}

export interface ProjectCreateInput {
  // ندعم الصيغتين معاً لضمان عدم حدوث خطأ 2345 في أي صفحة
  name?: string;
  client?: string;
  risk_level?: 'Low' | 'Moderate' | 'High' | 'Critical';
  status?: 'Active' | 'Review' | 'Compliant' | 'Planning';

  // حقول الباكيند المطلوبة
  project_name?: string;
  client_name?: string;
  sector?: string;
}

export interface ProjectUpdateInput extends Partial<ProjectCreateInput> {}