import { chatContract } from '@/service/contract/chat';
import { programsContract } from '@/service/contract/programs';

/** Router aggregation only: the types come from here; nothing uses it at run time. */
export const contract = {
  programs: programsContract,
  chat: chatContract
};
