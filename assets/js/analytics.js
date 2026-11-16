(function () {
  "use strict";
  let calculatorChanged = false;
  let calculatorTracked = false;
  let episodeChanged = false;
  const filteredEpisodes = new Set();

  // Only real control interactions qualify; rendering default values does not.
  function markCalculatorChange(event) {
    if (!event.isTrusted || !(event.target instanceof Element)) return;
    const control = event.target.closest('[id^="exp33-calculator-"]');
    if (control && !control.id.includes("save-upload")) calculatorChanged = true;
  }
  document.addEventListener("input", markCalculatorChange, true);
  document.addEventListener("change", markCalculatorChange, true);
  // Select options may be rendered in a portal outside the calculator.
  document.addEventListener("click", function (event) {
    if (event.isTrusted && event.target instanceof Element && event.target.closest("#xenosaga-tabs")) {
      episodeChanged = true;
    }
    if (event.target instanceof Element && event.target.closest('[role="option"]')) {
      const active = document.activeElement;
      if (active instanceof Element && active.closest('[id^="exp33-calculator-"]')) {
        markCalculatorChange({isTrusted: event.isTrusted, target: active});
      }
    }
  }, true);

  function track(name, properties) {
    // A blocked or unavailable analytics script must never break the tools.
    try {
      if (typeof window.rybbit?.event === "function") window.rybbit.event(name, properties);
    } catch (_) { /* Analytics is optional. */ }
  }
  const noUpdate = () => window.dash_clientside.no_update;
  window.dash_clientside = Object.assign({}, window.dash_clientside, {
    analytics: {
      calculator: function (_result, character, skill) {
        if (calculatorChanged && !calculatorTracked && character && skill) {
          calculatorTracked = true;
          track("calculator_used", {character: character, skill: skill});
        }
        return noUpdate();
      },
      saveImport: function (_message, color, isOpen) {
        if (isOpen) {
          track(color === "danger" ? "save_import_failed" : "save_import_succeeded", {});
        }
        return noUpdate();
      },
      xenosaga: function (episode, filters, cell) {
        const triggered = window.dash_clientside.callback_context.triggered || [];
        for (const trigger of triggered) {
          if (trigger.prop_id === "xenosaga-tabs.active_tab") {
            if (episodeChanged) track("xenosaga_episode_selected", {episode: episode});
            episodeChanged = false;
          } else if (trigger.prop_id === "xenosaga-grid.filterModel" &&
                     filters && Object.keys(filters).length && !filteredEpisodes.has(episode)) {
            filteredEpisodes.add(episode);
            track("xenosaga_table_filtered", {episode: episode});
          } else if (trigger.prop_id === "xenosaga-grid.cellClicked" && cell?.rowId) {
            track("xenosaga_enemy_details_opened", {episode: episode, enemy_id: String(cell.rowId)});
          }
        }
        return noUpdate();
      }
    }
  });
})();
