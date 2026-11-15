const RESULT_STYLES = {
  "Suitable within calendar constraints": "bg-field-100 text-field-800 border-field-300",
  "Conditionally feasible": "bg-earth-100 text-earth-600 border-earth-300",
  "Insufficient time window": "bg-rose-50 text-rose-700 border-rose-200",
  "Insufficient information": "bg-gray-100 text-gray-600 border-gray-300",
};

const CONFIDENCE_STYLES = {
  High: "bg-field-700 text-white",
  Medium: "bg-earth-500 text-white",
  Low: "bg-gray-400 text-white",
};

export function ResultBadge({ result }) {
  const style = RESULT_STYLES[result] || "bg-gray-100 text-gray-700 border-gray-300";
  return (
    <span className={`inline-flex items-center rounded-full border px-3 py-1 text-sm font-semibold ${style}`}>
      {result}
    </span>
  );
}

export function ConfidenceBadge({ confidence }) {
  const style = CONFIDENCE_STYLES[confidence] || "bg-gray-400 text-white";
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wide ${style}`}>
      Evidence: {confidence}
    </span>
  );
}

export function ValidationBadge({ status }) {
  if (status === "valid") return null;
  const label = status === "missing_inputs" ? "Missing information" : "Invalid dates";
  return (
    <span className="inline-flex items-center rounded-full border border-amber-300 bg-amber-50 px-2.5 py-0.5 text-xs font-semibold text-amber-700">
      {label}
    </span>
  );
}
