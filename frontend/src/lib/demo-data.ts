export type DemoJob = {
  id: string;
  title: string;
  company: string;
  location: string;
  workModel: 'Remote' | 'Hybrid' | 'Onsite';
  contractType: 'Full-time' | 'Part-time' | 'Contract';
  tags: string[];
  postedLabel: string;
  matched: boolean;
  matchScore?: number;
};

export const demoJobs: DemoJob[] = [
  {
    id: 'job-1',
    title: 'Senior Frontend Engineer',
    company: 'Corelight',
    location: 'Remote / EMEA',
    workModel: 'Remote',
    contractType: 'Full-time',
    tags: ['React', 'TypeScript', 'Design Systems'],
    postedLabel: '2h ago',
    matched: true,
    matchScore: 92
  },
  {
    id: 'job-2',
    title: 'Platform Engineer',
    company: 'Trendyol',
    location: 'Istanbul',
    workModel: 'Hybrid',
    contractType: 'Full-time',
    tags: ['Kubernetes', 'Go', 'Terraform'],
    postedLabel: '5h ago',
    matched: true,
    matchScore: 86
  },
  {
    id: 'job-3',
    title: 'Security Engineer',
    company: 'ScaleOps',
    location: 'Berlin',
    workModel: 'Onsite',
    contractType: 'Contract',
    tags: ['Python', 'Detection', 'Cloud'],
    postedLabel: '1d ago',
    matched: false
  },
  {
    id: 'job-4',
    title: 'Product Designer',
    company: 'Northstar',
    location: 'Munich',
    workModel: 'Hybrid',
    contractType: 'Full-time',
    tags: ['Figma', 'Research', 'Systems'],
    postedLabel: '2d ago',
    matched: false
  }
];

export const profileChecklist = [
  {id: 'fullName', label: 'Display name', complete: true},
  {id: 'phone', label: 'Phone number', complete: false},
  {id: 'headline', label: 'Headline', complete: true},
  {id: 'education', label: 'Education', complete: false},
  {id: 'skills', label: 'Skills', complete: true},
  {id: 'location', label: 'Location preferences', complete: true},
  {id: 'jobType', label: 'Job type preferences', complete: false},
  {id: 'notifications', label: 'Notification preferences', complete: true}
];
