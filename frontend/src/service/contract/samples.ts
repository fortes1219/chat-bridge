import { oc } from '@orpc/contract';
import { SampleQuestionsSchema } from '@/service/schema/sample';

/** The sample questions (oRPC, types only: nothing calls it at run time). */
export const samplesContract = {
  getSampleQuestions: oc
    .route({
      method: 'GET',
      path: '/chat/samples',
      summary: 'Questions about the sample news, while it is in the knowledge base'
    })
    .output(SampleQuestionsSchema)
};
