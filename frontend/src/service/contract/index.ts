import { chatContract } from '@/service/contract/chat';
import { programsContract } from '@/service/contract/programs';
import { samplesContract } from '@/service/contract/samples';
import { strategyContract } from '@/service/contract/strategy';

/** Router aggregation only: the types come from here; nothing uses it at run time. */
export const contract = {
  programs: programsContract,
  samples: samplesContract,
  chat: chatContract,
  strategy: strategyContract
};
