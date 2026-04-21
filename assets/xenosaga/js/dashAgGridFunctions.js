var dagfuncs = window.dashAgGridFunctions = window.dashAgGridFunctions || {};

// Extract the starting numeric value from a cell value.
// Handles plain numbers and range-like strings such as "100-200".
dagfuncs.extractRangeStart = function (params, fieldName) {
  if (!params || !params.data) {
    return null;
  }

  var rawValue = params.data[fieldName];
  if (rawValue === null || rawValue === undefined || rawValue === "") {
    return null;
  }

  if (typeof rawValue === "number") {
    return rawValue;
  }

  var firstPart = String(rawValue).split("-")[0].trim().replace(/,/g, "");
  var parsed = Number(firstPart);
  return Number.isNaN(parsed) ? null : parsed;
};

// Display numeric values with thousands separators while leaving nulls blank.
dagfuncs.formatNumberWithCommas = function (params) {
  var value = params ? params.value : null;
  if (value === null || value === undefined || value === "") {
    return "";
  }

  var numericValue = typeof value === "number" ? value : Number(String(value).replace(/,/g, ""));
  if (Number.isNaN(numericValue)) {
    return value;
  }

  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 20
  }).format(numericValue);
};

// Read a sibling field from the row for tooltip display.
dagfuncs.getLinkedFieldValue = function (params, fieldName) {
  if (!params || !params.data || !fieldName) {
    return null;
  }

  var value = params.data[fieldName];
  return value === null || value === undefined || value === "" ? null : value;
};

// Apply a subtle affordance when a drop has extra item details behind it.
dagfuncs.getItemDropCellStyle = function (params, effectField) {
  var hasEffect = Boolean(
    params &&
    params.data &&
    effectField &&
    params.data[effectField]
  );

  if (!hasEffect) {
    return null;
  }

  return {
    color: "var(--bs-link-color)",
    cursor: "help",
    textDecoration: "underline dotted",
    textUnderlineOffset: "0.18em"
  };
};
