import { useEffect, useLayoutEffect, useRef, useState } from 'react';

export interface ContextAction {
  id: string;
  label: string;
  shortcut?: string;
  disabled?: boolean;
}

export interface ContextMenuProps {
  x: number;
  y: number;
  nodeId: string | null;
  actions: ContextAction[];
  onRun: (id: string) => void;
  onClose: () => void;
}

/**
 * Node context menu.
 *
 * Rendered as text nodes into a positioned overlay — never as injected HTML —
 * and kept inside the viewport so it cannot open off-screen.
 */
export function ContextMenu(props: ContextMenuProps): JSX.Element {
  const { x, y, nodeId, actions, onRun, onClose } = props;
  const ref = useRef<HTMLDivElement | null>(null);
  const [position, setPosition] = useState({ x, y });

  useLayoutEffect(() => {
    const element = ref.current;
    if (!element) return;
    const rect = element.getBoundingClientRect();
    const maxX = window.innerWidth - rect.width - 8;
    const maxY = window.innerHeight - rect.height - 8;
    setPosition({
      x: Math.max(8, Math.min(x, maxX)),
      y: Math.max(8, Math.min(y, maxY)),
    });
  }, [x, y]);

  useEffect(() => {
    const onPointerDown = (event: MouseEvent) => {
      if (ref.current && !ref.current.contains(event.target as Node)) onClose();
    };
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') onClose();
    };
    // `capture` so the menu closes before the canvas consumes the click.
    window.addEventListener('mousedown', onPointerDown, true);
    window.addEventListener('keydown', onKeyDown);
    return () => {
      window.removeEventListener('mousedown', onPointerDown, true);
      window.removeEventListener('keydown', onKeyDown);
    };
  }, [onClose]);

  return (
    <div
      ref={ref}
      className="contextMenu"
      style={{ left: `${position.x}px`, top: `${position.y}px` }}
      role="menu"
      aria-label="Node actions"
    >
      <p className="contextMenu__title">{nodeId ? truncate(nodeId, 44) : 'Canvas'}</p>
      {actions.map((action) => (
        <button
          key={action.id}
          type="button"
          role="menuitem"
          className="contextMenu__item"
          disabled={action.disabled}
          onClick={() => onRun(action.id)}
        >
          <span>{action.label}</span>
          {action.shortcut && <span className="contextMenu__shortcut">{action.shortcut}</span>}
        </button>
      ))}
    </div>
  );
}

function truncate(value: string, max: number): string {
  return value.length > max ? `${value.slice(0, max - 1)}…` : value;
}
