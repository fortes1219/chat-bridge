import { useQuery } from '@tanstack/vue-query';
import { programKeys } from '@/queries/keys';
import { getPrograms, type ProgramState } from '@/service/api/programs';
import type { AppError } from '@/service/error';

/** The login states as server state; read again only through `refetch`. */
export function useProgramsQuery() {
  return useQuery<ProgramState[], AppError>({
    queryKey: programKeys.states(),
    queryFn: ({ signal }) => getPrograms(signal)
  });
}
