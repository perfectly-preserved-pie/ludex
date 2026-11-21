(() => {
    const navigation = window.navigation;
    if (!navigation || !document.startViewTransition) return;

    const reducedMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
    let activeTransition;

    navigation.addEventListener("navigate", (event) => {
        const destination = new URL(event.destination.url);
        if (!event.destination.sameDocument || destination.pathname === location.pathname) return;

        activeTransition?.cancel();
        const content = document.getElementById("_pages_content");
        if (reducedMotion.matches || !content?.firstElementChild) return;

        // Dash fetches the next layout after updating history. Wait for React to
        // commit it, but let slow requests render normally after a short deadline.
        const previousPage = content.firstElementChild;
        let complete;
        const updated = new Promise((resolve) => { complete = resolve; });
        const observer = new MutationObserver((records) => {
            if (records.some(({ target }) => target === content || target === previousPage)) {
                cleanup();
            }
        });
        observer.observe(content, { childList: true, subtree: true });

        const root = document.documentElement;
        root.classList.add("ludex-page-transition");
        const transition = document.startViewTransition(() => updated);
        const pending = {
            cancel() {
                transition.skipTransition();
                cleanup();
            },
        };
        const deadline = window.setTimeout(pending.cancel, 350);
        activeTransition = pending;

        function cleanup() {
            observer.disconnect();
            window.clearTimeout(deadline);
            complete();
        }

        transition.finished.finally(() => {
            cleanup();
            if (activeTransition === pending) {
                activeTransition = undefined;
                root.classList.remove("ludex-page-transition");
            }
        });
    });
})();
