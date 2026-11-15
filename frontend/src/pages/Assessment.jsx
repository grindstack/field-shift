import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { postAssess, ApiError } from "../api";
import { LoadingState, ErrorState } from "../components/Status";

const IRRIGATION_SOURCES = [
  { value: "", label: "Not specified" },
  { value: "canal", label: "Canal" },
  { value: "tubewell", label: "Tubewell / groundwater" },
  { value: "both", label: "Canal and tubewell" },
  { value: "rainfed", label: "Rainfed (no irrigation source)" },
  { value: "unknown", label: "Unknown" },
];

const IRRIGATION_AVAILABILITY = [
  { value: "", label: "Not specified" },
  { value: "available", label: "Available" },
  { value: "not_available", label: "Not available" },
  { value: "unknown", label: "Unknown" },
];

const initialState = {
  wheat_sow_date: "",
  wheat_harvest_date: "",
  rice_transplant_date: "",
  mungbean_sow_date: "",
  irrigation_source: "",
  irrigation_available: "",
  soil_ph: "",
  soil_texture_note: "",
};

export default function Assessment() {
  const [form, setForm] = useState(initialState);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const update = (field) => (e) => setForm((f) => ({ ...f, [field]: e.target.value }));

  async function handleSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setError(null);

    const soil_test =
      form.soil_ph || form.soil_texture_note
        ? {
            ph: form.soil_ph ? Number(form.soil_ph) : null,
            texture_note: form.soil_texture_note || null,
          }
        : null;

    const payload = {
      wheat_sow_date: form.wheat_sow_date || null,
      wheat_harvest_date: form.wheat_harvest_date || null,
      rice_transplant_date: form.rice_transplant_date || null,
      mungbean_sow_date: form.mungbean_sow_date || null,
      irrigation_source: form.irrigation_source || null,
      irrigation_available: form.irrigation_available || null,
      soil_test,
    };

    try {
      const result = await postAssess(payload);
      sessionStorage.setItem("fieldshift_assessment", JSON.stringify(result));
      navigate("/results");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Unexpected error while assessing.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-3xl px-4 py-10 sm:px-6">
      <h1 className="text-2xl font-bold text-field-900">Farmer assessment</h1>
      <p className="mt-2 text-sm text-field-700">
        Enter the dates you expect for this field. Fields left blank are not guessed -
        the assessment will report that information is missing rather than invent a date.
      </p>

      <div className="mt-4 rounded-lg border border-earth-200 bg-earth-50 p-4 text-sm text-earth-600">
        <p className="font-semibold text-field-900">About the two defaults used below</p>
        <ul className="mt-1 list-inside list-disc space-y-1">
          <li>
            <strong>Mungbean sowing assumption (7 days):</strong> if you don't provide an
            expected mungbean sowing date, the engine assumes it is sown 7 days after the
            wheat harvest (based on the single KSK trial). Supplying your own date always
            takes priority, and the assessment discloses which was used.
          </li>
          <li>
            <strong>Safety buffer (7 days):</strong> on top of the KSK trial's 65-70 day
            sowing-to-pod-picking estimate, a configurable 7-day safety margin is added
            before a calendar window is called clearly sufficient. This is a modeling
            choice, not a research finding.
          </li>
        </ul>
      </div>

      <form onSubmit={handleSubmit} className="mt-6 space-y-6">
        <fieldset className="rounded-lg border border-field-200 bg-white p-5">
          <legend className="px-1 text-sm font-semibold text-field-900">Baseline &amp; shared dates</legend>
          <div className="grid gap-4 sm:grid-cols-2">
            <DateField
              label="Expected wheat sowing date"
              value={form.wheat_sow_date}
              onChange={update("wheat_sow_date")}
              hint="Used to check the baseline against the ~20 Nov departmental guidance."
            />
            <DateField
              label="Expected wheat harvest date"
              value={form.wheat_harvest_date}
              onChange={update("wheat_harvest_date")}
              hint="Anchors both the baseline and the mungbean fallow window."
            />
          </div>
        </fieldset>

        <fieldset className="rounded-lg border border-field-200 bg-white p-5">
          <legend className="px-1 text-sm font-semibold text-field-900">Alternative scenario dates</legend>
          <div className="grid gap-4 sm:grid-cols-2">
            <DateField
              label="Expected next rice transplanting date"
              value={form.rice_transplant_date}
              onChange={update("rice_transplant_date")}
              hint="The end of the mungbean fallow window."
            />
            <DateField
              label="Expected mungbean sowing date (optional)"
              value={form.mungbean_sow_date}
              onChange={update("mungbean_sow_date")}
              hint="Leave blank to use the disclosed 7-day-after-harvest assumption."
            />
          </div>
        </fieldset>

        <fieldset className="rounded-lg border border-field-200 bg-white p-5">
          <legend className="px-1 text-sm font-semibold text-field-900">Irrigation</legend>
          <div className="grid gap-4 sm:grid-cols-2">
            <SelectField
              label="Irrigation source"
              value={form.irrigation_source}
              onChange={update("irrigation_source")}
              options={IRRIGATION_SOURCES}
            />
            <SelectField
              label="Reported irrigation availability"
              value={form.irrigation_available}
              onChange={update("irrigation_available")}
              options={IRRIGATION_AVAILABILITY}
            />
          </div>
          <p className="mt-2 text-xs text-field-500">
            This is recorded as a stated condition only. It is never treated as proof of
            water sufficiency - no water balance is calculated.
          </p>
        </fieldset>

        <fieldset className="rounded-lg border border-field-200 bg-white p-5">
          <legend className="px-1 text-sm font-semibold text-field-900">
            Optional farm soil-test information
          </legend>
          <div className="grid gap-4 sm:grid-cols-2">
            <TextField
              label="Soil pH (if known)"
              value={form.soil_ph}
              onChange={update("soil_ph")}
              type="number"
              step="0.1"
            />
            <TextField
              label="Texture / other notes"
              value={form.soil_texture_note}
              onChange={update("soil_texture_note")}
            />
          </div>
          <p className="mt-2 text-xs text-field-500">
            If supplied, this is shown alongside (and takes precedence over) the
            district-level SoilGrids context.
          </p>
        </fieldset>

        {error && <ErrorState message={error} />}
        {loading && <LoadingState label="Running the decision engine..." />}

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-md bg-field-700 px-5 py-3 text-sm font-semibold text-white shadow-sm hover:bg-field-800 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {loading ? "Assessing..." : "Run Assessment"}
        </button>
      </form>
    </div>
  );
}

function DateField({ label, value, onChange, hint }) {
  return (
    <label className="block text-sm">
      <span className="font-medium text-field-800">{label}</span>
      <input
        type="date"
        value={value}
        onChange={onChange}
        className="mt-1 w-full rounded-md border border-field-300 px-3 py-2 text-field-900 focus:border-field-600 focus:outline-none focus:ring-1 focus:ring-field-600"
      />
      {hint && <span className="mt-1 block text-xs text-field-500">{hint}</span>}
    </label>
  );
}

function SelectField({ label, value, onChange, options }) {
  return (
    <label className="block text-sm">
      <span className="font-medium text-field-800">{label}</span>
      <select
        value={value}
        onChange={onChange}
        className="mt-1 w-full rounded-md border border-field-300 px-3 py-2 text-field-900 focus:border-field-600 focus:outline-none focus:ring-1 focus:ring-field-600"
      >
        {options.map((opt) => (
          <option key={opt.value} value={opt.value}>
            {opt.label}
          </option>
        ))}
      </select>
    </label>
  );
}

function TextField({ label, value, onChange, type = "text", step }) {
  return (
    <label className="block text-sm">
      <span className="font-medium text-field-800">{label}</span>
      <input
        type={type}
        step={step}
        value={value}
        onChange={onChange}
        className="mt-1 w-full rounded-md border border-field-300 px-3 py-2 text-field-900 focus:border-field-600 focus:outline-none focus:ring-1 focus:ring-field-600"
      />
    </label>
  );
}
