import type { ColorMode, Palette } from '../graph/palette';
import type { FacetOptions } from '../graph/filters';

export interface LegendProps {
  palette: Palette;
  colorMode: ColorMode;
  facets: FacetOptions;
  communityMode: 'structural' | 'hybrid';
  communityCount: number;
}

/**
 * Always-visible legend.
 *
 * Only the encoding that is actually in use is shown: coloring by kind lists
 * kinds, coloring by community shows the categorical ramp plus the active
 * detection mode (structural vs hybrid mean different things and are not
 * comparable).
 */
export function Legend(props: LegendProps): JSX.Element {
  const { palette, colorMode, facets, communityMode, communityCount } = props;

  return (
    <div className="legend" aria-label="Graph legend">
      <div className="legend__group">
        <span className="legend__title">Nodes</span>
        <span className="legend__hint legend__hint--inline">
          size = importance &amp; degree
        </span>
      </div>

      {colorMode === 'kind' ? (
        <ul className="legend__items">
          {facets.kinds.slice(0, 18).map((kind) => (
            <li key={kind} className="legend__item">
              <span className="legend__swatch" style={{ background: palette.node[kind] ?? '#7f8ea3' }} />
              <span className="legend__label">{kind}</span>
            </li>
          ))}
          {facets.kinds.length === 0 && <li className="legend__item legend__item--muted">no data</li>}
        </ul>
      ) : (
        <div className="legend__group">
          <ul className="legend__items legend__items--ramp">
            {palette.communityRamp.slice(0, 12).map((color) => (
              <li key={color} className="legend__swatch legend__swatch--ramp" style={{ background: color }} />
            ))}
          </ul>
          <p className="legend__hint">
            <strong>{communityMode === 'structural' ? 'Structural' : 'Hybrid'}</strong> communities
            ({communityCount})
          </p>
        </div>
      )}

      <div className="legend__group">
        <span className="legend__title">Edges</span>
        <ul className="legend__items">
          <li className="legend__item">
            <span className="legend__line legend__line--solid" />
            <span className="legend__label">
              structural
              <span className="legend__sub">extracted / resolved</span>
            </span>
          </li>
          <li className="legend__item">
            <span className="legend__line legend__line--dashed" />
            <span className="legend__label">
              semantic
              <span className="legend__sub">embedding similarity</span>
            </span>
          </li>
          <li className="legend__item">
            <span className="legend__line legend__line--uncertain" />
            <span className="legend__label">
              inferred / ambiguous
              <span className="legend__sub">not a resolved fact</span>
            </span>
          </li>
        </ul>
      </div>

      <div className="legend__group">
        <span className="legend__title">Node rings</span>
        <ul className="legend__items">
          <li className="legend__item">
            <span className="legend__ring" style={{ borderColor: palette.selected }} />
            <span className="legend__label">selected</span>
          </li>
          <li className="legend__item">
            <span className="legend__ring" style={{ borderColor: palette.changed }} />
            <span className="legend__label">changed</span>
          </li>
          <li className="legend__item">
            <span className="legend__ring" style={{ borderColor: palette.unresolved }} />
            <span className="legend__label">unresolved</span>
          </li>
          <li className="legend__item">
            <span className="legend__ring" style={{ borderColor: palette.accent }} />
            <span className="legend__label">pinned</span>
          </li>
        </ul>
      </div>
    </div>
  );
}
