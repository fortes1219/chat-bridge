/** TanStack Query key factory. */
export const programKeys = {
  all: ['programs'] as const,
  states: () => [...programKeys.all, 'states'] as const
};
