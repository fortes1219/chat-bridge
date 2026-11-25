/** TanStack Query key factory. */
export const programKeys = {
  all: ['programs'] as const,
  states: () => [...programKeys.all, 'states'] as const
};

export const sampleKeys = {
  all: ['samples'] as const,
  questions: () => [...sampleKeys.all, 'questions'] as const
};

export const strategyKeys = {
  all: ['strategy'] as const,
  current: () => [...strategyKeys.all, 'current'] as const
};
