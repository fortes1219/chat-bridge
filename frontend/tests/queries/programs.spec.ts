import { beforeEach, describe, expect, it, vi } from 'vitest';
import { mount } from '@vue/test-utils';
import { defineComponent, h } from 'vue';
import { QueryClient, VueQueryPlugin } from '@tanstack/vue-query';
import { programKeys } from '@/queries/keys';

const getProgramsMock = vi.fn();
vi.mock('@/service/api/programs', () => ({
  getPrograms: () => getProgramsMock()
}));

import { useProgramsQuery } from '@/queries/use-programs-query';

beforeEach(() => {
  getProgramsMock.mockReset();
});

describe('programKeys', () => {
  it('states() is stable and namespaced', () => {
    expect(programKeys.states()).toEqual(['programs', 'states']);
  });
});

describe('useProgramsQuery', () => {
  it('returns the API function’s data and reads again only on refetch', async () => {
    getProgramsMock.mockResolvedValue([{ program: 'codex', state: 'logged in' }]);
    let refetch: () => Promise<unknown> = async () => undefined;

    const Probe = defineComponent({
      setup() {
        const query = useProgramsQuery();
        refetch = query.refetch;
        return () => h('div', JSON.stringify(query.data.value ?? null));
      }
    });
    const queryClient = new QueryClient({ defaultOptions: { queries: { retry: false } } });
    const wrapper = mount(Probe, { global: { plugins: [[VueQueryPlugin, { queryClient }]] } });

    await vi.waitFor(() => expect(wrapper.text()).toContain('logged in'));
    expect(getProgramsMock).toHaveBeenCalledTimes(1);

    await refetch();
    expect(getProgramsMock).toHaveBeenCalledTimes(2);
  });
});
