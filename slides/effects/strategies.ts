import type { allocationExamples, retrievalExamples } from './data.ts'

interface StrategyByEffect {
  none: { effect: 'none' }
  'layered-cover': { effect: 'layered-cover' }
  'document-chunks': { effect: 'document-chunks' }
  'rank-fusion': { effect: 'rank-fusion' }
  'retrieval-3d': {
    effect: 'retrieval-3d'
    example: keyof typeof retrievalExamples
    view: 'baseline' | 'comparison'
  }
  'evaluation-recall': { effect: 'evaluation-recall' }
  'retrieval-tradeoffs': { effect: 'retrieval-tradeoffs' }
  'allocation-compare': { effect: 'allocation-compare'; example: keyof typeof allocationExamples }
  'transport-flow': { effect: 'transport-flow' }
}

export type SlideEffectStrategy = StrategyByEffect[keyof StrategyByEffect]
export type SlideEffectKey = keyof StrategyByEffect

export const effectSteps = {
  none: 0,
  'layered-cover': 0,
  'document-chunks': 2,
  'rank-fusion': 2,
  'retrieval-3d': 1,
  'evaluation-recall': 2,
  'retrieval-tradeoffs': 3,
  'allocation-compare': 0,
  'transport-flow': 2,
} satisfies Record<SlideEffectKey, number>

export const effectsBySlide = {
  cover: { effect: 'layered-cover' },
  workflow: { effect: 'none' },
  corpus: { effect: 'none' },
  normalization: { effect: 'none' },
  ingest: { effect: 'document-chunks' },
  hybrid: { effect: 'rank-fusion' },
  failure: { effect: 'retrieval-3d', example: 'multi-topic-query', view: 'baseline' },
  retrieval: { effect: 'retrieval-3d', example: 'multi-topic-query', view: 'comparison' },
  evaluation: { effect: 'evaluation-recall' },
  tradeoffs: { effect: 'retrieval-tradeoffs' },
  grounding: { effect: 'none' },
  proposal: { effect: 'allocation-compare', example: 'sample-profile' },
  controls: { effect: 'none' },
  operations: { effect: 'transport-flow' },
  delivery: { effect: 'none' },
  limits: { effect: 'none' },
} as const satisfies Record<string, SlideEffectStrategy>

export type SlideId = keyof typeof effectsBySlide

export function effectFor(id: unknown): SlideEffectStrategy | undefined {
  if (typeof id === 'string' && Object.hasOwn(effectsBySlide, id))
    return effectsBySlide[id as SlideId]
}

export function clickCountFor(id: unknown) {
  return effectSteps[effectFor(id)?.effect ?? 'none']
}
