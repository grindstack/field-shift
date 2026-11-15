import { Link } from "react-router-dom";

export default function Dashboard() {
  return (
    <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
      <section className="rounded-2xl border border-field-200 bg-white p-8 shadow-sm">
        <p className="text-xs font-semibold uppercase tracking-wide text-field-500">
          Field Shift &middot; Pilot location: Sheikhupura, Punjab, Pakistan
        </p>
        <h1 className="mt-2 text-3xl font-bold text-field-900 sm:text-4xl">
          A transparent, calendar-based crop rotation assessment
        </h1>
        <p className="mt-4 max-w-3xl text-field-700">
          Field Shift compares the standard basmati rice &rarr; wheat rotation against an
          alternative that inserts a short mungbean catch crop before the next rice
          transplant. The assessment is rule-based and evidence-tagged: it checks whether
          there is enough calendar time, discloses which dates were farmer-supplied versus
          assumed, and never claims more certainty than the underlying research supports.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <Link
            to="/assess"
            className="rounded-md bg-field-700 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-field-800"
          >
            Assess Crop Rotation
          </Link>
          <Link
            to="/climate"
            className="rounded-md border border-field-300 bg-white px-5 py-2.5 text-sm font-semibold text-field-800 hover:bg-field-50"
          >
            View Historical Climate Context
          </Link>
        </div>
      </section>

      <section className="mt-8 grid gap-4 sm:grid-cols-3">
        <InfoTile label="Historical data coverage" value="2016 - 2025" detail="NASA POWER, IMERG, Landsat NDVI, MODIS LST" />
        <InfoTile label="Static district context" value="SoilGrids + SRTM" detail="Single sample point, district-level only" />
        <InfoTile label="Decision logic" value="Rule-based, no ML" detail="Every result ships with reasons, confidence, and limitations" />
      </section>

      <section className="mt-10">
        <h2 className="text-lg font-semibold text-field-900">Datasets behind this assessment</h2>
        <div className="mt-3 overflow-x-auto rounded-lg border border-field-200 bg-white">
          <table className="w-full min-w-160 text-left text-sm">
            <thead className="bg-field-50 text-field-600">
              <tr>
                <th className="px-4 py-2 font-semibold">Dataset</th>
                <th className="px-4 py-2 font-semibold">Role</th>
                <th className="px-4 py-2 font-semibold">Period</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-field-100">
              <Row dataset="NASA POWER (daily / monthly)" role="Air temperature, humidity, wind, solar, rainfall - historical context" period="2016-2025" />
              <Row dataset="IMERG (monthly rainfall)" role="Primary rainfall figure, compared against POWER precipitation" period="2016-2025" />
              <Row dataset="Landsat NDVI (monthly)" role="Optional vegetation-greenness context - never crop identification" period="2016-2025" />
              <Row dataset="MODIS LST (monthly)" role="Land-surface temperature context - never treated as air temperature" period="2016-2025" />
              <Row dataset="SoilGrids + SRTM (static)" role="District-level soil/terrain background - never a farm-level measurement" period="single sample point" />
            </tbody>
          </table>
        </div>
        <p className="mt-2 text-xs text-field-500">
          Observation-coverage columns (image/scene counts) are excluded from every
          agricultural measurement shown in this tool.
        </p>
      </section>

      <section className="mt-10 grid gap-5 sm:grid-cols-2">
        <ScenarioCard
          title="Baseline"
          sequence="Basmati rice → wheat"
          description="The dominant local rotation. Assessed against the farmer's own wheat sowing and harvest dates and the sourced Punjab calendar guidance."
          accent="field"
        />
        <ScenarioCard
          title="Alternative"
          sequence="Basmati rice → wheat → mungbean → next rice"
          description="Adds a short mungbean catch crop in the fallow window. Feasibility depends on calendar fit; capped at Conditionally feasible under current evidence because the mungbean window's irrigation need is never independently verified."
          accent="earth"
        />
      </section>
    </div>
  );
}

function InfoTile({ label, value, detail }) {
  return (
    <div className="rounded-lg border border-field-200 bg-white p-4">
      <p className="text-xs font-medium uppercase tracking-wide text-field-500">{label}</p>
      <p className="mt-1 text-xl font-bold text-field-900">{value}</p>
      <p className="mt-1 text-xs text-field-600">{detail}</p>
    </div>
  );
}

function Row({ dataset, role, period }) {
  return (
    <tr>
      <td className="px-4 py-2 font-medium text-field-900">{dataset}</td>
      <td className="px-4 py-2 text-field-700">{role}</td>
      <td className="px-4 py-2 text-field-600">{period}</td>
    </tr>
  );
}

function ScenarioCard({ title, sequence, description, accent }) {
  const accentClasses =
    accent === "field"
      ? "border-field-300 bg-field-50"
      : "border-earth-300 bg-earth-50";
  return (
    <div className={`rounded-xl border p-5 ${accentClasses}`}>
      <p className="text-xs font-semibold uppercase tracking-wide text-field-600">{title}</p>
      <p className="mt-1 text-lg font-bold text-field-900">{sequence}</p>
      <p className="mt-2 text-sm text-field-700">{description}</p>
    </div>
  );
}
