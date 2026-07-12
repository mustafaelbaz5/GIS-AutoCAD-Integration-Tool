/**
 * Shared JS<->Python bridge helper, per Iteration 4 Task C §8.2.D.
 *
 * Wraps every `window.pywebview.api.*` call so callers never touch
 * try/catch or the pywebview readiness dance directly, and pushes from
 * Python land as `window.onProgressUpdate(payload)` (or any other
 * `window.<name>` the API pushes to) without a page reload.
 */

const Bridge = (() => {
  /** Resolves once pywebview has injected `window.pywebview.api`. */
  function ready() {
    if (window.pywebview && window.pywebview.api) {
      return Promise.resolve();
    }
    return new Promise((resolve) => {
      window.addEventListener('pywebviewready', () => resolve(), { once: true });
    });
  }

  /**
   * Call `window.pywebview.api[methodName](...args)`, surfacing any
   * failure as a friendly Arabic message rather than letting it throw
   * past the caller.
   *
   * @returns {Promise<{ok: true, value: any} | {ok: false, error: string}>}
   */
  async function call(methodName, ...args) {
    try {
      await ready();
      const api = window.pywebview.api;
      if (typeof api[methodName] !== 'function') {
        throw new Error(`Unknown API method: ${methodName}`);
      }
      const value = await api[methodName](...args);
      return { ok: true, value };
    } catch (err) {
      console.error(`Bridge call failed: ${methodName}`, err);
      return { ok: false, error: 'حدث خطأ أثناء الاتصال بالتطبيق. حاول مرة أخرى.' };
    }
  }

  /**
   * Register a handler for a Python-to-JS push, e.g.
   * `onPush('onProgressUpdate', (payload) => { ... })`. Python calls
   * this by name via `window.evaluate_js('window.onProgressUpdate(...)')`.
   */
  function onPush(functionName, handler) {
    window[functionName] = handler;
  }

  return { ready, call, onPush };
})();
