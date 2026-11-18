import type { RefObject } from "preact";
import { useLayoutEffect, useRef, useState } from "preact/hooks";

/** The laid-out width of an element, so a drawing can use real pixels instead of stretching. */
export function useWidth<T extends Element>(initial: number): [RefObject<T>, number] {
  const ref = useRef<T>(null);
  const [width, setWidth] = useState(initial);
  useLayoutEffect(() => {
    const element = ref.current;
    if (!element) return;
    const observer = new ResizeObserver(() => setWidth(Math.max(120, element.clientWidth)));
    observer.observe(element);
    setWidth(Math.max(120, element.clientWidth));
    return () => observer.disconnect();
  }, []);
  return [ref, width];
}
