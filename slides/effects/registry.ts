import { defineAsyncComponent, type Component } from 'vue'
import type { SlideEffectKey } from './strategies.ts'

export const effectComponents = {
  none: null,
  'layered-cover': defineAsyncComponent(() => import('../components/LayeredCover.vue')),
  'document-chunks': defineAsyncComponent(() => import('../components/DocumentChunks.vue')),
  'rank-fusion': defineAsyncComponent(() => import('../components/RankFusion.vue')),
  'retrieval-3d': defineAsyncComponent(() => import('../components/RetrievalEffect.vue')),
  'evaluation-recall': defineAsyncComponent(() => import('../components/EvaluationResults.vue')),
  'retrieval-tradeoffs': defineAsyncComponent(() => import('../components/RetrievalTradeoffs.vue')),
  'allocation-compare': defineAsyncComponent(() => import('../components/AllocationCompare.vue')),
  'transport-flow': defineAsyncComponent(() => import('../components/TransportFlow.vue')),
} satisfies Record<SlideEffectKey, Component | null>
