import {getEmployerCopy} from '@/lib/employer-copy';

export type {EmployerNavItem, EmployerNavSection} from '@/lib/employer-copy';

export function getEmployerNavSections(locale: string) {
  return getEmployerCopy(locale).nav.sections;
}

export function getEmployerQuickActions(locale: string) {
  return getEmployerCopy(locale).nav.quickActions;
}
