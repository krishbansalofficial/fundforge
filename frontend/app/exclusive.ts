/** Run `fn` unless a previous call through the same flag is still in flight; returns whether it ran.
 *  The flag is a ref, so a double-click in one tick is dropped before React re-renders the button. */
export async function exclusive(flag: { current: boolean }, fn: () => Promise<void>): Promise<boolean> {
  if (flag.current) return false;
  flag.current = true;
  try {
    await fn();
    return true;
  } finally {
    flag.current = false;
  }
}
