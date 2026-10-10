import {
  IconFilters,
  IconGraph,
  IconSettings,
  IconShield,
  IconSliders,
} from './Icons';

/**
 * Persistent icon rail.
 *
 * The exploration panels used to hold a fixed width open at all times, which
 * on a graph viewer is the most valuable screen real estate there is. The rail
 * keeps every panel one click away and takes width only while a panel is open.
 */
export interface RailProps {
  active: 'filters' | 'graph' | 'settings' | null;
  onToggle: (panel: 'filters' | 'graph' | 'settings') => void;
  onPrivacy: () => void;
}

const PANELS = [
  { id: 'filters' as const, label: 'Filters', Icon: IconFilters },
  { id: 'graph' as const, label: 'Graph options', Icon: IconSliders },
  { id: 'settings' as const, label: 'Settings', Icon: IconSettings },
];

export function Rail({ active, onToggle, onPrivacy }: RailProps): JSX.Element {
  return (
    <nav className="rail" aria-label="Workspace panels">
      {PANELS.map(({ id, label, Icon }) => (
        <button
          key={id}
          type="button"
          className="rail__button"
          aria-current={active === id}
          aria-expanded={active === id}
          aria-label={label}
          title={label}
          onClick={() => onToggle(id)}
        >
          <Icon size={17} />
        </button>
      ))}
      <span className="rail__spacer" />
      <span className="rail__divider" aria-hidden="true" />
      <button
        type="button"
        className="rail__button"
        aria-label="Privacy and egress"
        title="Privacy and egress"
        onClick={onPrivacy}
      >
        <IconShield size={17} />
      </button>
      <button
        type="button"
        className="rail__button"
        aria-label="Graph view"
        title="Graph view"
        onClick={() => onToggle('graph')}
      >
        <IconGraph size={17} />
      </button>
    </nav>
  );
}