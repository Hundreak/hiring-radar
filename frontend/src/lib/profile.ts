import {profileChecklist} from '@/lib/demo-data';

export function getProfileCompletion(): number {
  const completed = profileChecklist.filter((item) => item.complete).length;
  return (completed / profileChecklist.length) * 100;
}
