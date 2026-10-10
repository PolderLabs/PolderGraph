/**
 * Interface icons.
 *
 * Inline SVG rather than text glyphs: the previous characters (⚙, ☾, ≡, ◇) were
 * rendered by whatever font the browser happened to pick, so they shifted
 * between platforms and had no accessible name. Each icon here is drawn on the
 * same 16px grid with a consistent stroke weight, and every use is labelled by
 * its surrounding control.
 */

export interface IconProps {
  size?: number;
  className?: string;
}

function svgProps({ size = 16, className }: IconProps) {
  return {
    width: size,
    height: size,
    viewBox: '0 0 16 16',
    fill: 'none',
    stroke: 'currentColor',
    strokeWidth: 1.5,
    strokeLinecap: 'round' as const,
    strokeLinejoin: 'round' as const,
    className,
    'aria-hidden': true,
    focusable: false as const,
  };
}

export function IconFilters(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <path d="M2 4h12M4.5 8h7M7 12h2" />
    </svg>
  );
}

export function IconGraph(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <circle cx="4" cy="4" r="1.6" />
      <circle cx="12" cy="6" r="1.6" />
      <circle cx="6" cy="12" r="1.6" />
      <path d="M5.4 4.9 10.6 5.4M4.7 5.4l.9 5M10.9 7.3 7.2 10.7" />
    </svg>
  );
}

export function IconTheme(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <path d="M13 9.4A5.5 5.5 0 0 1 6.6 3a5.5 5.5 0 1 0 6.4 6.4Z" />
    </svg>
  );
}

export function IconSun(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <circle cx="8" cy="8" r="3" />
      <path d="M8 1.5v1.4M8 13.1v1.4M1.5 8h1.4M13.1 8h1.4M3.4 3.4l1 1M11.6 11.6l1 1M12.6 3.4l-1 1M4.4 11.6l-1 1" />
    </svg>
  );
}

export function IconSettings(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <circle cx="8" cy="8" r="2.1" />
      <path d="M8 1.6v1.6M8 12.8v1.6M1.6 8h1.6M12.8 8h1.6M3.5 3.5l1.1 1.1M11.4 11.4l1.1 1.1M12.5 3.5l-1.1 1.1M4.6 11.4l-1.1 1.1" />
    </svg>
  );
}

export function IconSearch(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <circle cx="7" cy="7" r="4.2" />
      <path d="m10.2 10.2 3 3" />
    </svg>
  );
}

export function IconClose(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <path d="m4 4 8 8M12 4l-8 8" />
    </svg>
  );
}

export function IconRefresh(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <path d="M13.5 8a5.5 5.5 0 1 1-1.9-4.2" />
      <path d="M13.7 2.2v3.1h-3.1" />
    </svg>
  );
}

export function IconFit(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <path d="M2 5.5V3a1 1 0 0 1 1-1h2.5M14 5.5V3a1 1 0 0 0-1-1h-2.5M2 10.5V13a1 1 0 0 0 1 1h2.5M14 10.5V13a1 1 0 0 1-1 1h-2.5" />
    </svg>
  );
}

export function IconPause(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <path d="M6 3.5v9M10 3.5v9" />
    </svg>
  );
}

export function IconPlay(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <path d="M5 3.2 12 8l-7 4.8Z" />
    </svg>
  );
}

export function IconDownload(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <path d="M8 2.5v7.5M4.8 7.2 8 10.4l3.2-3.2M2.8 13.2h10.4" />
    </svg>
  );
}

export function IconSave(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <path d="M3 2.8h7.6L13 5.2v8H3Z" />
      <path d="M5.5 2.8v3.6h5V2.8M5.5 13.2v-3.6h5v3.6" />
    </svg>
  );
}

export function IconShield(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <path d="M8 1.8 13.2 4v4c0 3.2-2.2 5.4-5.2 6.4C5 13.4 2.8 11.2 2.8 8V4Z" />
      <path d="m5.9 8 1.5 1.5 2.8-3" />
    </svg>
  );
}

export function IconSliders(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <path d="M2.5 5h7M12 5h1.5M2.5 11h1.5M6.5 11h7" />
      <circle cx="10.8" cy="5" r="1.7" />
      <circle cx="5.2" cy="11" r="1.7" />
    </svg>
  );
}

export function IconKey(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <circle cx="5.5" cy="6" r="3" />
      <path d="M7.8 7.8 13.5 13.5M10.8 10.8l1.7-.3M12.5 12.5l1.3-.3" />
    </svg>
  );
}

export function IconHelp(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <circle cx="8" cy="8" r="6.2" />
      <path d="M6.2 6.4a2 2 0 0 1 3.6 1.1c0 1.2-1.8 1.5-1.8 2.5M8 12.2h.1" />
    </svg>
  );
}

export function IconChevron(props: IconProps) {
  return (
    <svg {...svgProps(props)}>
      <path d="m6 3.5 5 4.5-5 4.5" />
    </svg>
  );
}