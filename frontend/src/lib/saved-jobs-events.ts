/**
 * Cross-page saved-jobs state synchronization via custom events.
 *
 * When a job is saved or unsaved on any page, dispatch an event so other
 * mounted pages can update their local `savedJobIds` without a full reload.
 */

export const SAVED_JOBS_CHANGED_EVENT = 'coresift:saved-jobs-changed';

export type SavedJobsChangedDetail = {
  jobId: number;
  action: 'saved' | 'unsaved';
};

export function dispatchSavedJobsChanged(detail: SavedJobsChangedDetail) {
  if (typeof window === 'undefined') return;
  window.dispatchEvent(
    new CustomEvent<SavedJobsChangedDetail>(SAVED_JOBS_CHANGED_EVENT, {detail}),
  );
}

export function onSavedJobsChanged(
  handler: (detail: SavedJobsChangedDetail) => void,
): () => void {
  if (typeof window === 'undefined') return () => {};
  const listener = (e: Event) => {
    const detail = (e as CustomEvent<SavedJobsChangedDetail>).detail;
    if (detail) handler(detail);
  };
  window.addEventListener(SAVED_JOBS_CHANGED_EVENT, listener);
  return () => window.removeEventListener(SAVED_JOBS_CHANGED_EVENT, listener);
}
