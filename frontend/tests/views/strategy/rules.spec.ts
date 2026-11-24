import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { flushPromises, type VueWrapper } from '@vue/test-utils';
import type { RulesInput, Strategy } from '@/service/api/strategy';
import type { AppError } from '@/service/error';
import { PROPOSAL, PROPOSED_RULE_CHECKS, RULE_CHECKS, STRATEGY } from '../../helpers/strategy';
import { mountView } from '../../helpers/mount';

const getStrategyMock = vi.fn<() => Promise<Strategy>>();
const saveRulesMock = vi.fn<(input: RulesInput) => Promise<Strategy>>();
vi.mock('@/service/api/strategy', () => ({
  getStrategy: () => getStrategyMock(),
  decideProposal: vi.fn(),
  saveRules: (input: RulesInput) => saveRulesMock(input)
}));

import StrategyPanel from '@/views/strategy/StrategyPanel.vue';

/** The fixture's rules as the page sends them: the settings, without the results. */
const SAVED_RULES: RulesInput['rules'] = RULE_CHECKS.rules.map(({ kind, limit_percent, market, enabled }) => ({
  kind,
  limit_percent,
  market,
  enabled
}));

let wrapper: VueWrapper | undefined;

beforeEach(() => {
  getStrategyMock.mockReset().mockResolvedValue(STRATEGY);
  saveRulesMock.mockReset();
});

afterEach(() => {
  wrapper?.unmount();
  wrapper = undefined;
  document.body.innerHTML = '';
});

// Mounted on its own, the panel is in the page's default language, Traditional Chinese.
async function mountPanel(): Promise<VueWrapper> {
  ({ wrapper } = await mountView(StrategyPanel));
  await flushPromises();
  return wrapper;
}

async function openEditor(): Promise<VueWrapper> {
  const page = await mountPanel();
  await page.find('[data-test="rules-edit"]').trigger('click');
  return page;
}

function saveButton(page: VueWrapper) {
  return page.find('[data-test="rules-save"]');
}

describe('the rule checks', () => {
  it('say how many rules are met, each one’s result, and that targets are checked', async () => {
    const page = await mountPanel();

    expect(page.find('[data-test="rules-summary"]').text()).toBe('符合 2 / 3 條規則');
    expect(page.find('[data-test="rule-0"]').text()).toContain('任一標的最多 40%');
    expect(page.find('[data-test="rule-0"]').text()).toContain('最高 50%');
    expect(page.find('[data-test="rule-breaking-0"]').text()).toBe('不符合的：台積電');
    expect(page.find('[data-test="rule-status-0"]').text()).toBe('不符合');
    expect(page.find('[data-test="rule-status-1"]').text()).toBe('符合');
    expect(page.find('[data-test="rule-2"]').text()).toContain('美股合計最多 30%');
    expect(page.find('[data-test="rules-note"]').text()).toContain('目標比例');
  });

  it('say a rule that is off is off, and count only the rules that are on', async () => {
    const [first, ...rest] = RULE_CHECKS.rules;
    getStrategyMock.mockResolvedValue({
      ...STRATEGY,
      rule_checks: {
        met: 2,
        enabled: 2,
        rules: [{ ...first!, enabled: false, met: null, measured: null, breaking: [] }, ...rest]
      }
    });

    const page = await mountPanel();

    expect(page.find('[data-test="rules-summary"]').text()).toBe('符合 2 / 2 條規則');
    expect(page.find('[data-test="rule-status-0"]').text()).toBe('關閉');
    expect(page.find('[data-test="rule-breaking-0"]').exists()).toBe(false);
  });
});

describe('the rule editor', () => {
  it('sends nothing until a rule is changed', async () => {
    const page = await openEditor();

    expect(saveButton(page).attributes('disabled')).toBeDefined();
    await saveButton(page).trigger('click');
    expect(saveRulesMock).not.toHaveBeenCalled();
  });

  it('saves a changed limit with every rule in order, and shows the checks the service returns', async () => {
    saveRulesMock.mockResolvedValue({ ...STRATEGY, rule_checks: { ...RULE_CHECKS, met: 3 } });
    const page = await openEditor();

    page.findAllComponents({ name: 'InputNumber' })[0]!.vm.$emit('update:modelValue', 50);
    await flushPromises();
    await saveButton(page).trigger('click');
    await flushPromises();

    expect(saveRulesMock).toHaveBeenCalledTimes(1);
    expect(saveRulesMock).toHaveBeenCalledWith({
      rules: [{ ...SAVED_RULES[0]!, limit_percent: 50 }, SAVED_RULES[1], SAVED_RULES[2]]
    });
    expect(page.find('[data-test="rule-editor"]').exists()).toBe(false);
    expect(page.find('[data-test="rules-summary"]').text()).toBe('符合 3 / 3 條規則');
  });

  it('keeps the limit when the field is emptied', async () => {
    const page = await openEditor();

    page.findAllComponents({ name: 'InputNumber' })[0]!.vm.$emit('update:modelValue', null);
    await flushPromises();

    expect(saveButton(page).attributes('disabled')).toBeDefined();
  });

  it('turns a rule off, adds one that limits nothing, and removes one', async () => {
    saveRulesMock.mockResolvedValue(STRATEGY);
    const page = await openEditor();

    page.findAllComponents({ name: 'Switch' })[1]!.vm.$emit('update:modelValue', false);
    await page.find('[data-test="rule-add"]').trigger('click');
    await page.find('[data-test="rule-remove-0"]').trigger('click');
    await saveButton(page).trigger('click');
    await flushPromises();

    expect(saveRulesMock).toHaveBeenCalledWith({
      rules: [
        { ...SAVED_RULES[1]!, enabled: false },
        SAVED_RULES[2],
        { kind: 'max_holding_weight', limit_percent: 100, market: null, enabled: true }
      ]
    });
  });

  it('gives a rule that becomes a market rule a market, and takes it away when it stops being one', async () => {
    saveRulesMock.mockResolvedValue(STRATEGY);
    const page = await openEditor();

    // The kind selects are in the rows' order; the third row also has its market select.
    const selects = page.findAllComponents({ name: 'Select' });
    selects[0]!.vm.$emit('update:modelValue', 'max_market_weight');
    selects[2]!.vm.$emit('update:modelValue', 'min_holding_weight');
    await flushPromises();
    await saveButton(page).trigger('click');
    await flushPromises();

    expect(saveRulesMock).toHaveBeenCalledWith({
      rules: [
        { ...SAVED_RULES[0]!, kind: 'max_market_weight', market: 'TW' },
        SAVED_RULES[1],
        { ...SAVED_RULES[2]!, kind: 'min_holding_weight', market: null }
      ]
    });
  });

  it('stays open with the person’s changes and says why when the service refuses them', async () => {
    const refused: AppError = {
      source: 'backend',
      code: 'rejected',
      reason: 'rule_limit_out_of_range',
      message: 'rule 1: 101% is outside 0 to 100',
      status: 422
    };
    saveRulesMock.mockRejectedValue(refused);
    const page = await openEditor();

    page.findAllComponents({ name: 'InputNumber' })[0]!.vm.$emit('update:modelValue', 45);
    await flushPromises();
    await saveButton(page).trigger('click');
    await flushPromises();

    const error = page.find('[data-test="rules-error"]');
    expect(error.text()).toContain('0 到 100%');
    expect(error.text()).not.toContain('outside');
    expect(page.find('[data-test="rule-editor"]').exists()).toBe(true);
    expect(saveButton(page).attributes('disabled')).toBeUndefined();
  });

  it('leaves the rules as they were when the person cancels', async () => {
    const page = await openEditor();

    page.findAllComponents({ name: 'InputNumber' })[0]!.vm.$emit('update:modelValue', 50);
    await page.find('[data-test="rules-cancel"]').trigger('click');
    await page.find('[data-test="rules-edit"]').trigger('click');
    await flushPromises();

    expect(saveRulesMock).not.toHaveBeenCalled();
    expect(saveButton(page).attributes('disabled')).toBeDefined();
  });
});

describe('a proposal', () => {
  it('shows each rule’s result on the current and on the proposed targets', async () => {
    getStrategyMock.mockResolvedValue({ ...STRATEGY, proposal: PROPOSAL });

    const page = await mountPanel();

    expect(page.find('[data-test="rule-before-0"]').text()).toBe('不符合');
    expect(page.find('[data-test="rule-after-0"]').text()).toBe('符合');
    expect(page.find('[data-test="rule-after-2"]').text()).toBe('符合');
    const summary = page.find('[data-test="rule-diff-summary"]').text();
    expect(summary).toContain(`符合 ${RULE_CHECKS.met} / 3 條規則`);
    expect(summary).toContain(`符合 ${PROPOSED_RULE_CHECKS.met} / 3 條規則`);
  });
});
