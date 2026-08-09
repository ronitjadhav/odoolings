import { cn } from '@/lib/cn';
import { ArrowSquareOut } from '@phosphor-icons/react/dist/ssr/ArrowSquareOut';
import { Book } from '@phosphor-icons/react/dist/ssr/Book';
import { ChatCircle } from '@phosphor-icons/react/dist/ssr/ChatCircle';
import { CheckCircle } from '@phosphor-icons/react/dist/ssr/CheckCircle';
import { CodeBlock } from '@phosphor-icons/react/dist/ssr/CodeBlock';
import { Database } from '@phosphor-icons/react/dist/ssr/Database';
import { Flag } from '@phosphor-icons/react/dist/ssr/Flag';
import { Gear } from '@phosphor-icons/react/dist/ssr/Gear';
import { GitBranch } from '@phosphor-icons/react/dist/ssr/GitBranch';
import { GithubLogo } from '@phosphor-icons/react/dist/ssr/GithubLogo';
import { GraduationCap } from '@phosphor-icons/react/dist/ssr/GraduationCap';
import { MagnifyingGlass } from '@phosphor-icons/react/dist/ssr/MagnifyingGlass';
import { Newspaper } from '@phosphor-icons/react/dist/ssr/Newspaper';
import { Package } from '@phosphor-icons/react/dist/ssr/Package';
import { PlayCircle } from '@phosphor-icons/react/dist/ssr/PlayCircle';
import { RedditLogo } from '@phosphor-icons/react/dist/ssr/RedditLogo';
import { Rocket } from '@phosphor-icons/react/dist/ssr/Rocket';
import { ShoppingBag } from '@phosphor-icons/react/dist/ssr/ShoppingBag';
import { Stack } from '@phosphor-icons/react/dist/ssr/Stack';
import { Target } from '@phosphor-icons/react/dist/ssr/Target';
import { TreeStructure } from '@phosphor-icons/react/dist/ssr/TreeStructure';
import { Users } from '@phosphor-icons/react/dist/ssr/Users';
import { Warning } from '@phosphor-icons/react/dist/ssr/Warning';
import { Wrench } from '@phosphor-icons/react/dist/ssr/Wrench';
import { XCircle } from '@phosphor-icons/react/dist/ssr/XCircle';
import { YoutubeLogo } from '@phosphor-icons/react/dist/ssr/YoutubeLogo';

/**
 * The site's whole icon vocabulary, in one place, on purpose. A curated
 * allow-list beats a `name: string` prop that dynamically imports anything in
 * the library: every entry here is a real static import, so the bundle only
 * ever grows by icons actually in use, and a typo in an .mdx file is a build
 * failure, not a blank space in production. Add to this list before reaching
 * for a one-off import in a chapter.
 */
export const ICONS = {
  // "Further reading" / "Where the knowledge lives" link kinds
  docs: Book,
  source: GithubLogo,
  video: YoutubeLogo,
  talk: PlayCircle,
  forum: ChatCircle,
  reddit: RedditLogo,
  store: ShoppingBag,
  news: Newspaper,
  external: ArrowSquareOut,
  // recurring concepts, for Card eyebrows and inline emphasis
  database: Database,
  module: Package,
  branch: GitBranch,
  inheritance: TreeStructure,
  layers: Stack,
  code: CodeBlock,
  people: Users,
  tool: Wrench,
  settings: Gear,
  search: MagnifyingGlass,
  goal: Target,
  milestone: Flag,
  rocket: Rocket,
  learn: GraduationCap,
  // status
  ok: CheckCircle,
  warn: Warning,
  fail: XCircle,
} as const;

export type IconName = keyof typeof ICONS;

/**
 * `weight="regular"` and `size="1em"` are the library defaults; both are set
 * explicitly here so an icon always matches the surrounding text's line
 * height and never fights a parent's `font-size`. Fill is `currentColor`
 * (also the default), which is why no theme wiring is needed: it inherits
 * whatever color the surrounding prose already has in light or dark mode.
 */
export function Icon({
  name,
  size = '1em',
  weight = 'regular',
  className,
}: {
  name: IconName;
  size?: string | number;
  weight?: 'thin' | 'light' | 'regular' | 'bold' | 'fill' | 'duotone';
  className?: string;
}) {
  const Glyph = ICONS[name];
  return (
    <Glyph
      size={size}
      weight={weight}
      // Tailwind's preflight sets every <svg> to `display: block`, which is
      // right for a 400px diagram and wrong for a glyph sitting inside a
      // sentence: unset it here or the icon pushes onto its own line. -0.15em
      // is a hand-picked nudge, not a formula; Phosphor's glyphs sit a touch
      // high against Geist's baseline at 1em, and this is where they matched.
      className={cn('inline-block align-[-0.15em]', className)}
      aria-hidden="true"
    />
  );
}
