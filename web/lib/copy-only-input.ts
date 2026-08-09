import type { Element } from 'hast';
import type { ShikiTransformer } from 'shiki';

// Prompts that mark a line as something the reader typed, in the order chapters use them:
// shell ($), Python REPL (>>> and its ... continuation), and psql (<db>=#).
const PROMPTS = [/^\$ /, /^>>> /, /^\.\.\. /, /^[a-zA-Z_]\w*=# /];

/**
 * ```console blocks mix typed commands with their real output so the chapter can quote
 * exact results. The copy button has no way to tell them apart, so copying a block pastes
 * the output right along with the command. This strips the leading prompt from typed lines
 * (so paste-to-terminal doesn't paste a literal "$") and drops output lines from the copy
 * entirely, via fumadocs' existing `.nd-copy-ignore` convention. Display is untouched.
 */
export function transformerCopyOnlyInput(): ShikiTransformer {
  return {
    name: 'odoolings:copy-only-input',
    line(hast: Element, line: number) {
      if (this.options.lang !== 'console') return;

      const raw = this.source.split('\n')[line - 1] ?? '';
      const prompt = PROMPTS.find((re) => re.test(raw));

      if (!prompt) {
        this.addClassToHast(hast, 'nd-copy-ignore');
        return;
      }

      const match = raw.match(prompt);
      const promptText = match ? match[0] : '';
      const first = hast.children[0];
      // Only handle the shape every console block actually renders: one span holding the
      // whole line's text (this project has no real "console" grammar, so there's no
      // per-token highlighting to fight with). Anything else, leave display alone rather
      // than risk mangling it.
      if (
        promptText &&
        first &&
        first.type === 'element' &&
        first.children.length === 1 &&
        first.children[0].type === 'text' &&
        first.children[0].value === raw
      ) {
        const promptSpan: Element = {
          type: 'element',
          tagName: first.tagName,
          properties: { ...first.properties },
          children: [{ type: 'text', value: promptText }],
        };
        this.addClassToHast(promptSpan, 'nd-copy-ignore');
        first.children[0].value = raw.slice(promptText.length);
        hast.children.unshift(promptSpan);
      }
    },
  };
}
