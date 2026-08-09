'use client';
import { useEffect, useId, useState } from 'react';

export function Mermaid({
  chart,
  label = 'Diagram',
  wide = false,
}: {
  chart: string;
  label?: string;
  /** Render at natural width and scroll sideways, instead of scaling to fit. */
  wide?: boolean;
}) {
  const id = useId().replace(/[^a-zA-Z0-9]/g, '');
  const [svg, setSvg] = useState('');
  const [error, setError] = useState(false);
  const [theme, setTheme] = useState<'dark' | 'default'>('default');

  useEffect(() => {
    const root = document.documentElement;
    const updateTheme = () => setTheme(root.classList.contains('dark') ? 'dark' : 'default');
    updateTheme();
    const observer = new MutationObserver(updateTheme);
    observer.observe(root, { attributes: true, attributeFilter: ['class'] });
    return () => observer.disconnect();
  }, []);

  useEffect(() => {
    let active = true;
    setError(false);
    void (async () => {
      try {
        const { default: mermaid } = await import('mermaid');
        mermaid.initialize({ startOnLoad: false, theme, fontFamily: 'inherit' });
        const out = await mermaid.render(`m${id}`, chart.trim());
        if (active) setSvg(out.svg);
      } catch {
        if (active) setError(true);
      }
    })();
    return () => {
      active = false;
    };
  }, [chart, id, theme]);

  if (error) {
    return <p role="alert">This diagram could not be rendered.</p>;
  }

  return (
    <div
      role="img"
      aria-label={label}
      // Diagrams are centred and capped at the container, which is right for the
      // flowcharts that make up almost all of them. `wide` opts out: a timeline
      // spanning years has a large natural width, and capping it scales the whole
      // SVG down until the labels are unreadable. Those scroll sideways instead.
      className={
        wide
          ? 'my-6 overflow-x-auto'
          : 'my-6 flex justify-center overflow-x-auto [&_svg]:max-w-full'
      }
      dangerouslySetInnerHTML={{ __html: svg }}
    />
  );
}
