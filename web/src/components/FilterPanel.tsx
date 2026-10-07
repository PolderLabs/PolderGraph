import { useState } from 'react';
import type { FacetOptions } from '../graph/filters';
import type { FiltersState, ForceSettingsState } from '../state/preferences';
import { DEFAULT_FORCE } from '../state/preferences';
import { COMMUNITY_MODE_EXPLANATION, type CommunityMode } from '../graph/community';

export interface FilterPanelProps {
  facets: FacetOptions;
  filters: FiltersState;
  visibleCount: number;
  totalCount: number;
  communityMode: CommunityMode;
  onChange: (next: FiltersState) => void;
  onReset: () => void;
}

/**
 * Explorer panel. Every facet here is applied client-side against the payload
 * that is already loaded, so toggling one is instantaneous and never a request.
 */
export function FilterPanel(props: FilterPanelProps): JSX.Element {
  const { facets, filters } = props;
  const [openSections, setOpenSections] = useState<Record<string, boolean>>({
    text: true,
    kinds: true,
    languages: false,
    roots: false,
    communities: false,
    edges: true,
    provenance: false,
    visibility: true,
  });

  const update = (patch: Partial<FiltersState>) => props.onChange({ ...filters, ...patch });

  const setFlag = (field: keyof FiltersState, key: string, value: boolean): void => {
    update({ [field]: { ...(filters[field] as Record<string, boolean>), [key]: value } });
  };

  const toggleSection = (section: string) =>
    setOpenSections((previous) => ({ ...previous, [section]: !previous[section] }));

  return (
    <aside className="filters" aria-label="Filters and explorer">
      <div className="filters__header">
        <h2>Explore</h2>
        <button type="button" className="filters__reset" onClick={props.onReset}>
          reset
        </button>
      </div>

      <p className="filters__count">
        <strong>{props.visibleCount.toLocaleString()}</strong> of {props.totalCount.toLocaleString()} nodes
      </p>

      <label className="field">
        <span className="field__label">Text</span>
        <input
          type="search"
          className="field__input"
          value={filters.text}
          placeholder="name, path, kind…"
          onChange={(event) => update({ text: event.target.value })}
        />
      </label>

      <Facet
        title="Node kinds"
        open={openSections.kinds}
        onToggle={() => toggleSection('kinds')}
        values={facets.kinds}
        selected={filters.kinds}
        onToggleValue={(key) => setFlag('kinds', key, !filters.kinds[key])}
      />

      <Facet
        title="Languages"
        open={openSections.languages}
        onToggle={() => toggleSection('languages')}
        values={facets.languages}
        selected={filters.languages}
        onToggleValue={(key) => setFlag('languages', key, !filters.languages[key])}
      />

      <Facet
        title="Roots"
        open={openSections.roots}
        onToggle={() => toggleSection('roots')}
        values={facets.roots}
        selected={filters.roots}
        onToggleValue={(key) => setFlag('roots', key, !filters.roots[key])}
      />

      <Facet
        title={`Communities (${props.communityMode})`}
        open={openSections.communities}
        onToggle={() => toggleSection('communities')}
        values={facets.communities}
        selected={filters.communities}
        onToggleValue={(key) => setFlag('communities', key, !filters.communities[key])}
        hint={COMMUNITY_MODE_EXPLANATION[props.communityMode]}
      />

      <Facet
        title="Edge types"
        open={openSections.edges}
        onToggle={() => toggleSection('edges')}
        values={facets.edgeTypes}
        selected={filters.edgeTypes}
        onToggleValue={(key) => setFlag('edgeTypes', key, !filters.edgeTypes[key])}
      />

      <Facet
        title="Provenance"
        open={openSections.provenance}
        onToggle={() => toggleSection('provenance')}
        values={facets.provenance}
        selected={filters.provenance}
        onToggleValue={(key) => setFlag('provenance', key, !filters.provenance[key])}
      />

      <section className="filters__section">
        <label className="slider">
          <span className="slider__label">
            Minimum semantic similarity
            <strong>{filters.minSimilarity.toFixed(2)}</strong>
          </span>
          <input
            type="range"
            min={0}
            max={1}
            step={0.05}
            value={filters.minSimilarity}
            onChange={(event) => update({ minSimilarity: Number(event.target.value) })}
          />
          <span className="slider__hint">Applies to semantic edges only; structural facts are never thresholded.</span>
        </label>
      </section>

      <section className="filters__section">
        <h3 className="filters__sectionTitle">Visibility</h3>
        <Toggle
          label="Hide generated"
          checked={filters.hideGenerated}
          onChange={(value) => update({ hideGenerated: value })}
        />
        <Toggle
          label="Hide external"
          checked={filters.hideExternal}
          onChange={(value) => update({ hideExternal: value })}
        />
        <Toggle
          label="Only tests"
          checked={filters.onlyTests}
          onChange={(value) => update({ onlyTests: value })}
        />
        <Toggle
          label="Only docs"
          checked={filters.onlyDocs}
          onChange={(value) => update({ onlyDocs: value })}
        />
        <Toggle
          label="Only source"
          checked={filters.onlySource}
          onChange={(value) => update({ onlySource: value })}
        />
        <Toggle
          label="Only media"
          checked={filters.onlyMedia}
          onChange={(value) => update({ onlyMedia: value })}
        />
        <Toggle
          label="Changed since Git base"
          checked={filters.changedSinceGitBase}
          onChange={(value) => update({ changedSinceGitBase: value })}
        />
      </section>
    </aside>
  );
}

interface FacetProps {
  title: string;
  open: boolean;
  onToggle: () => void;
  values: string[];
  selected: Record<string, boolean>;
  onToggleValue: (key: string) => void;
  hint?: string;
}

function Facet({ title, open, onToggle, values, selected, onToggleValue, hint }: FacetProps): JSX.Element {
  const activeCount = values.filter((value) => selected[value]).length;
  return (
    <section className="filters__section">
      <button type="button" className="filters__sectionTitle filters__sectionTitle--button" onClick={onToggle} aria-expanded={open}>
        <span className={open ? 'caret caret--open' : 'caret'} aria-hidden="true" />
        {title}
        {activeCount > 0 && <span className="filters__badge">{activeCount}</span>}
      </button>
      {open && (
        <>
          {hint && <p className="filters__hint">{hint}</p>}
          {values.length === 0 ? (
            <p className="filters__empty">not present in this view</p>
          ) : (
            <ul className="facet">
              {values.map((value) => (
                <li key={value}>
                  <label className="facet__item">
                    <input
                      type="checkbox"
                      checked={selected[value] === true}
                      onChange={() => onToggleValue(value)}
                    />
                    <span className="facet__label">{value}</span>
                  </label>
                </li>
              ))}
            </ul>
          )}
        </>
      )}
    </section>
  );
}

function Toggle({
  label,
  checked,
  onChange,
}: {
  label: string;
  checked: boolean;
  onChange: (value: boolean) => void;
}): JSX.Element {
  return (
    <label className="toggle">
      <input type="checkbox" checked={checked} onChange={(event) => onChange(event.target.checked)} />
      <span>{label}</span>
    </label>
  );
}

export interface ForcePanelProps {
  settings: ForceSettingsState;
  open: boolean;
  canPreventOverlap: boolean;
  onToggleOpen: () => void;
  onChange: (settings: ForceSettingsState) => void;
  onReset: () => void;
}

/**
 * Advanced layout controls. Most users should never open this; it exists for
 * the cases where the default force layout does not suit a particular graph.
 */
export function ForcePanel(props: ForcePanelProps): JSX.Element {
  const { settings } = props;

  const set = (patch: Partial<ForceSettingsState>) =>
    props.onChange({ ...settings, ...patch });

  return (
    <section className={props.open ? 'force force--open' : 'force'}>
      <button
        type="button"
        className="force__toggle"
        onClick={props.onToggleOpen}
        aria-expanded={props.open}
      >
        <span className={props.open ? 'caret caret--open' : 'caret'} aria-hidden="true" />
        Force layout
      </button>

      {props.open && (
        <div className="force__body">
          <ForceSlider
            label="Gravity"
            value={settings.gravity}
            min={0}
            max={20}
            step={0.1}
            onChange={(value) => set({ gravity: value })}
          />
          <ForceSlider
            label="Scaling ratio"
            value={settings.scalingRatio}
            min={0.01}
            max={10}
            step={0.01}
            onChange={(value) => set({ scalingRatio: value })}
          />
          <ForceSlider
            label="Speed (inverse of slow-down)"
            value={1 / Math.max(settings.slowDown, 0.01)}
            min={0.05}
            max={5}
            step={0.05}
            onChange={(value) => set({ slowDown: 1 / Math.max(value, 0.01) })}
          />
          <ForceSlider
            label="Edge weight influence"
            value={settings.edgeWeightInfluence}
            min={0}
            max={5}
            step={0.1}
            onChange={(value) => set({ edgeWeightInfluence: value })}
          />
          <ForceToggle
            label="Strong gravity"
            checked={settings.strongGravityMode}
            onChange={(value) => set({ strongGravityMode: value })}
          />
          <ForceToggle
            label="Prevent overlap"
            checked={settings.adjustSizes}
            disabled={!props.canPreventOverlap}
            hint={
              props.canPreventOverlap
                ? 'Quadratic per iteration; disabled automatically above 4,000 nodes.'
                : 'Unavailable above 4,000 nodes — it would stall the browser.'
            }
            onChange={(value) => set({ adjustSizes: value })}
          />
          <ForceToggle
            label="Lin-log mode"
            checked={settings.linLogMode}
            onChange={(value) => set({ linLogMode: value })}
          />
          <ForceToggle
            label="Outbound attraction distribution"
            checked={settings.outboundAttractionDistribution}
            onChange={(value) => set({ outboundAttractionDistribution: value })}
          />
          <button type="button" className="force__reset" onClick={props.onReset}>
            Reset to defaults
          </button>
        </div>
      )}
    </section>
  );
}

function ForceSlider({
  label,
  value,
  min,
  max,
  step,
  onChange,
}: {
  label: string;
  value: number;
  min: number;
  max: number;
  step: number;
  onChange: (value: number) => void;
}): JSX.Element {
  return (
    <label className="force__field">
      <span className="force__label">
        {label}
        <strong>{value.toFixed(2)}</strong>
      </span>
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
      />
    </label>
  );
}

function ForceToggle({
  label,
  checked,
  onChange,
  disabled = false,
  hint,
}: {
  label: string;
  checked: boolean;
  onChange: (value: boolean) => void;
  disabled?: boolean;
  hint?: string;
}): JSX.Element {
  return (
    <label className={disabled ? 'force__field force__field--disabled' : 'force__field'}>
      <span className="force__label">
        <input
          type="checkbox"
          checked={checked}
          disabled={disabled}
          onChange={(event) => onChange(event.target.checked)}
        />
        {label}
      </span>
      {hint && <span className="force__hint">{hint}</span>}
    </label>
  );
}

export { DEFAULT_FORCE };
