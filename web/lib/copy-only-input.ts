import type { Element } from 'hast';
import type { ShikiTransformer } from 'shiki';

// Prompts that mark a line as something the reader typed, in the order chapters use them:
// shell ($), Python REPL (>>> and its ... continuation), and psql (<db>=#).
const PROMPTS = [/^\$ /, /^>>> /, /^\.\.\. /, /^[a-zA-Z_]\w*=# /];

// Only these fences mix typed input with real output.
const PROMPTED_LANGS = new Set(['console', 'python']);

/**
 * ```console and ```python blocks mix typed input with real output, so the chapter can
 * quote exact results. A naive copy grabs everything: the leading "$"/">>>" prompt (which
 * makes a pasted command fail outright) and the output lines sitting between commands
 * (which get replayed as bogus input). This computes the real typed-input text straight
 * from the block's raw source, prompts stripped and non-prompt lines dropped entirely, and
 * stores it as `data-copy` on the `<pre>` node. `components/copy-button.tsx` copies that
 * string verbatim instead of reading the rendered DOM, so it no longer matters how many
 * spans real syntax highlighting splits a prompt line into, or that a whole-line removal
 * and an inline prompt removal need different handling, both of which broke the previous
 * approach (built on fumadocs' `.nd-copy-ignore` convention, designed for neither case).
 */
export function transformerCopyOnlyInput(): ShikiTransformer {
  return {
    name: 'odoolings:copy-only-input',
    pre(hast: Element) {
      if (!PROMPTED_LANGS.has(this.options.lang as string)) return;

      const typed: string[] = [];
      for (const raw of this.source.split('\n')) {
        const prompt = PROMPTS.find((re) => re.test(raw));
        if (prompt) typed.push(raw.replace(prompt, ''));
      }

      hast.properties = { ...hast.properties, 'data-copy': typed.join('\n') };
    },
  };
}
