import assert from 'node:assert/strict'
import { readFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { parse } from '@slidev/parser/core'
import { allocationExamples, retrievalExamples } from '../effects/data.ts'
import { effectFor, effectsBySlide, effectSteps } from '../effects/strategies.ts'

function validateExample(strategy, id) {
  switch (strategy.effect) {
    case 'none':
    case 'layered-cover':
    case 'document-chunks':
    case 'rank-fusion':
    case 'evaluation-recall':
    case 'retrieval-tradeoffs':
    case 'transport-flow':
      assert.deepEqual(Object.keys(strategy), ['effect'], `${id}: unexpected effect parameters`)
      break
    case 'retrieval-3d':
      assert.deepEqual(Object.keys(strategy).sort(), ['effect', 'example', 'view'], `${id}: unexpected effect parameters`)
      assert(Object.hasOwn(retrievalExamples, strategy.example), `${id}: unknown retrieval example`)
      assert(['baseline', 'comparison'].includes(strategy.view), `${id}: unknown retrieval view`)
      break
    case 'allocation-compare':
      assert.deepEqual(Object.keys(strategy).sort(), ['effect', 'example'], `${id}: unexpected effect parameters`)
      assert(Object.hasOwn(allocationExamples, strategy.example), `${id}: unknown allocation example`)
      break
    default:
      assert.fail(`${id}: unknown effect ${strategy.effect}`)
  }
}

for (const locale of ['zh-TW', 'en']) {
  const file = fileURLToPath(new URL(`../slides.${locale}.md`, import.meta.url))
  const { slides } = await parse(await readFile(file, 'utf8'), file)
  const ids = new Set()
  for (const [index, { frontmatter }] of slides.entries()) {
    const context = `slides.${locale}.md slide ${index + 1}`
    const { slideId, layout } = frontmatter
    assert(!Object.hasOwn(frontmatter, 'effect'), `${context}: configure effects in strategies.ts`)
    assert(typeof slideId === 'string' && slideId !== '', `${context}: missing slideId`)
    assert(!ids.has(slideId), `${context}: duplicate slideId ${slideId}`)
    const strategy = effectFor(slideId)
    assert(strategy, `${context}: no strategy for ${slideId}`)
    if (effectSteps[strategy.effect])
      assert(!Object.hasOwn(frontmatter, 'clicks'), `${context}: the effect owns the click count`)
    assert(layout === 'research', `${context}: expected the research layout`)
    assert(frontmatter.locale === locale, `${context}: expected locale ${locale}`)
    validateExample(strategy, slideId)
    ids.add(slideId)
  }
  assert.deepEqual([...ids].sort(), Object.keys(effectsBySlide).sort(), `slides.${locale}.md: slideId set differs from the strategy map`)
  console.log(`Checked ${ids.size} slides for ${locale}.`)
}
