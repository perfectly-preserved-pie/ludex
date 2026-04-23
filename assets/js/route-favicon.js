(function () {
  const DEFAULT_FAVICON = "/assets/favicon/favicon.ico";
  const XENOSAGA_FAVICON = "/assets/xenosaga/favicon.png";

  function isXenosagaPath(pathname) {
    return pathname === "/xenosaga" || pathname.startsWith("/xenosaga/");
  }

  function faviconForPath(pathname) {
    return isXenosagaPath(pathname) ? XENOSAGA_FAVICON : DEFAULT_FAVICON;
  }

  function upsertFaviconLink(rel, href) {
    let link = document.head.querySelector('link[rel="' + rel + '"]');
    if (!link) {
      link = document.createElement("link");
      link.rel = rel;
      document.head.appendChild(link);
    }

    if (link.getAttribute("href") !== href) {
      link.setAttribute("href", href);
    }
  }

  function updateFavicon() {
    const href = faviconForPath(window.location.pathname);
    upsertFaviconLink("icon", href);
    upsertFaviconLink("shortcut icon", href);
  }

  function scheduleUpdate() {
    window.requestAnimationFrame(updateFavicon);
  }

  const originalPushState = window.history.pushState;
  window.history.pushState = function () {
    const result = originalPushState.apply(this, arguments);
    scheduleUpdate();
    return result;
  };

  const originalReplaceState = window.history.replaceState;
  window.history.replaceState = function () {
    const result = originalReplaceState.apply(this, arguments);
    scheduleUpdate();
    return result;
  };

  window.addEventListener("popstate", scheduleUpdate);
  window.addEventListener("DOMContentLoaded", scheduleUpdate);
  scheduleUpdate();
})();
