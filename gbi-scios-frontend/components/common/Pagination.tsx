// components/common/Pagination.tsx

"use client";

import { ChevronLeft, ChevronRight } from "lucide-react";

interface PaginationProps {
  /** Current page, 1-indexed. */
  page: number;
  /** Items per page. */
  pageSize: number;
  /** Total item count (may be the full backend list length if backend
   * doesn't return a separate `total` field). */
  total: number;
  /** Called when the user picks a different page. */
  onPageChange: (page: number) => void;
  /** Optional compact label override; defaults to "Showing X–Y of Z". */
  label?: string;
}

/**
 * Minimal dark-theme prev/next + page-number pagination.
 *
 * Used by ProjectsTable and the reports page (audit item C-1/P-18).
 * Client-side slicing is performed by the parent — this component only
 * renders the controls and calls onPageChange.
 */
export default function Pagination({
  page,
  pageSize,
  total,
  onPageChange,
  label,
}: PaginationProps) {
  const totalPages = Math.max(1, Math.ceil(total / pageSize));
  const safePage = Math.min(Math.max(1, page), totalPages);

  const start = total === 0 ? 0 : (safePage - 1) * pageSize + 1;
  const end = Math.min(safePage * pageSize, total);

  const go = (p: number): void => {
    const next = Math.min(Math.max(1, p), totalPages);
    if (next !== safePage) onPageChange(next);
  };

  if (total === 0) return null;

  return (
    <div className="flex items-center justify-between px-4 py-3 border-t border-slate-800 text-xs text-slate-400 bg-slate-950/40">
      <span className="hidden sm:inline">
        {label ?? `Showing ${start}–${end} of ${total}`}
      </span>
      <div className="flex items-center gap-1 ml-auto">
        <button
          type="button"
          onClick={() => go(safePage - 1)}
          disabled={safePage <= 1}
          className="p-1.5 rounded-md border border-slate-800 bg-slate-900 hover:bg-slate-800 hover:text-slate-200 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          aria-label="Previous page"
        >
          <ChevronLeft className="w-3.5 h-3.5" />
        </button>
        <span className="px-3 py-1 rounded-md bg-slate-900 border border-slate-800 text-slate-200 font-mono">
          {safePage} / {totalPages}
        </span>
        <button
          type="button"
          onClick={() => go(safePage + 1)}
          disabled={safePage >= totalPages}
          className="p-1.5 rounded-md border border-slate-800 bg-slate-900 hover:bg-slate-800 hover:text-slate-200 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          aria-label="Next page"
        >
          <ChevronRight className="w-3.5 h-3.5" />
        </button>
      </div>
    </div>
  );
}
