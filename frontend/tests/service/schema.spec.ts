import { describe, expect, it } from 'vitest';
import { ErrorBodySchema } from '@/service/schema/common';
import { ProgramStateSchema } from '@/service/schema/program';
import { ChatEventSchema, ChatRequestSchema, StreamErrorSchema } from '@/service/schema/chat';
import { CONTEXT_EVENT, textEvent } from '../helpers/sse';

describe('ProgramStateSchema', () => {
  it('accepts each program and state the service sends', () => {
    expect(ProgramStateSchema.parse({ program: 'claude-code', state: 'logged in' })).toEqual({
      program: 'claude-code',
      state: 'logged in'
    });
    expect(ProgramStateSchema.parse({ program: 'codex', state: 'not installed' }).state).toBe('not installed');
  });

  it('strict: an extra field, such as the program’s own status text, is refused', () => {
    expect(() => ProgramStateSchema.parse({ program: 'codex', state: 'unknown', detail: 'a@b.c' })).toThrow();
  });

  it('refuses a program or state the contract does not have', () => {
    expect(() => ProgramStateSchema.parse({ program: 'gemini', state: 'logged in' })).toThrow();
    expect(() => ProgramStateSchema.parse({ program: 'codex', state: 'maybe' })).toThrow();
  });
});

describe('ChatRequestSchema', () => {
  it('accepts a question with or without a program', () => {
    expect(ChatRequestSchema.parse({ question: 'q' })).toEqual({ question: 'q' });
    expect(ChatRequestSchema.parse({ question: 'q', program: 'codex' })).toEqual({ question: 'q', program: 'codex' });
  });

  it('refuses an empty question and one longer than the service takes', () => {
    expect(() => ChatRequestSchema.parse({ question: '' })).toThrow();
    expect(() => ChatRequestSchema.parse({ question: 'x'.repeat(10_241) })).toThrow();
  });
});

describe('ChatEventSchema', () => {
  it('accepts the context, with a source that has no event date', () => {
    const parsed = ChatEventSchema.parse(CONTEXT_EVENT);
    expect(parsed.type).toBe('response.context');
  });

  it('accepts a piece of the answer', () => {
    expect(ChatEventSchema.parse(textEvent('降息。'))).toEqual(textEvent('降息。'));
  });

  it('refuses a piece without its text and a context without its notice', () => {
    expect(() => ChatEventSchema.parse({ type: 'response.output_text.delta', delta: null, context: null })).toThrow();
    const withoutNotice = Object.fromEntries(
      Object.entries(CONTEXT_EVENT.context).filter(([key]) => key !== 'disclaimer')
    );
    expect(() => ChatEventSchema.parse({ ...CONTEXT_EVENT, context: withoutNotice })).toThrow();
  });

  it('refuses an event type the contract does not have', () => {
    expect(() => ChatEventSchema.parse({ type: 'response.done', delta: null, context: null })).toThrow();
  });
});

describe('ErrorBodySchema and StreamErrorSchema', () => {
  it('accept the service’s two error shapes, each with its reason', () => {
    const refused = { detail: { code: 'knowledge_base_empty', message: 'the knowledge base is empty' } };
    expect(ErrorBodySchema.parse(refused)).toEqual(refused);
    const failed = { code: 'not_logged_in', message: 'Claude Code is not logged in' };
    expect(StreamErrorSchema.parse(failed)).toEqual(failed);
  });

  it('refuse a reason the contract does not have, and a message without its reason', () => {
    expect(() => StreamErrorSchema.parse({ code: 'other', message: 'x' })).toThrow();
    expect(() => StreamErrorSchema.parse({ message: 'the program stopped' })).toThrow();
  });

  it('refuse FastAPI’s validation list, which the page never causes', () => {
    expect(() => ErrorBodySchema.parse({ detail: [{ msg: 'x' }] })).toThrow();
  });
});
