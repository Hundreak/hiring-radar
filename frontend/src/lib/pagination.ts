export const DEFAULT_LIST_PAGE_SIZE = 24;
export const DEFAULT_SAVED_PAGE_SIZE = 25;
export const DEFAULT_EMPLOYER_PAGE_SIZE = 12;

export type PaginationParams = {
  page?: number;
  pageSize?: number;
};

export type PaginationMeta = {
  page: number;
  pageSize: number;
  totalItems: number;
  totalPages: number;
};

export type PageSizeOption = 12 | 24 | 25 | 50;

export const DEFAULT_PAGE_SIZE_OPTIONS: PageSizeOption[] = [12, 24, 50];
export const SAVED_PAGE_SIZE_OPTIONS: PageSizeOption[] = [25, 50];

export function normalizePage(value: number | null | undefined): number {
  if (!Number.isFinite(value ?? NaN)) return 1;
  return Math.max(1, Math.floor(value as number));
}

export function normalizePageSize(
  value: number | null | undefined,
  fallback = DEFAULT_LIST_PAGE_SIZE,
  max = 50
): number {
  if (!Number.isFinite(value ?? NaN)) return fallback;
  return Math.min(max, Math.max(1, Math.floor(value as number)));
}

export function createPaginationMeta({
  page,
  pageSize,
  totalItems,
  totalPages,
}: {
  page?: number | null;
  pageSize?: number | null;
  totalItems?: number | null;
  totalPages?: number | null;
}): PaginationMeta {
  const normalizedPageSize = normalizePageSize(pageSize, DEFAULT_LIST_PAGE_SIZE);
  const normalizedTotalItems = Math.max(0, Number.isFinite(totalItems ?? NaN) ? Number(totalItems) : 0);
  const fallbackTotalPages =
    normalizedTotalItems === 0 ? 0 : Math.ceil(normalizedTotalItems / normalizedPageSize);

  return {
    page: normalizePage(page),
    pageSize: normalizedPageSize,
    totalItems: normalizedTotalItems,
    totalPages: Math.max(0, Number.isFinite(totalPages ?? NaN) ? Number(totalPages) : fallbackTotalPages),
  };
}

export function buildPaginationQuery(params: PaginationParams = {}) {
  const searchParams = new URLSearchParams();
  if (typeof params.page === 'number') {
    searchParams.set('page', String(normalizePage(params.page)));
  }
  if (typeof params.pageSize === 'number') {
    searchParams.set('page_size', String(normalizePageSize(params.pageSize)));
  }
  return searchParams;
}

export function paginateClientItems<T>(items: T[], page: number, pageSize: number): T[] {
  const safePage = normalizePage(page);
  const safePageSize = normalizePageSize(pageSize);
  const start = (safePage - 1) * safePageSize;
  return items.slice(start, start + safePageSize);
}

export function getPageRange(meta: PaginationMeta): {start: number; end: number} {
  if (meta.totalItems === 0 || meta.totalPages === 0) {
    return {start: 0, end: 0};
  }
  const start = (meta.page - 1) * meta.pageSize + 1;
  const end = Math.min(meta.totalItems, meta.page * meta.pageSize);
  return {start, end};
}
