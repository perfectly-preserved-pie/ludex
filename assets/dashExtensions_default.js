// Mirror Mantine's color scheme onto Bootstrap's theme attribute.
(function syncBootstrapTheme() {
  const root = document.documentElement;

  const applyTheme = () => {
    const scheme = root.getAttribute("data-mantine-color-scheme");
    if (scheme === "dark" || scheme === "light") {
      root.setAttribute("data-bs-theme", scheme);
    }
  };

  applyTheme();

  const observer = new MutationObserver((mutations) => {
    for (const mutation of mutations) {
      if (mutation.type === "attributes" && mutation.attributeName === "data-mantine-color-scheme") {
        applyTheme();
      }
    }
  });

  observer.observe(root, { attributes: true, attributeFilter: ["data-mantine-color-scheme"] });
})();
