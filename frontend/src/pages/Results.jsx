import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { ResultBadge, ConfidenceBadge, ValidationBadge } from "../components/ResultBadge";
import MungbeanWindowBar from "../components/MungbeanWindowBar";

export default function Results() {
  const [data, setData] = useState(null);

  useEffect(() => {
    const raw = sessionStorage.getItem("fieldshift_assessment");
    if (raw) {
      try {
        setData(JSON.parse(raw));
      } catch {
        setData(null);
      }
    }
  }, []);

  if (!data) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-16 text-center sm:px-6">
        <p className="text-field-700">No assessment has been run yet in this session.</p>
        <Link
          to="/assess"
          className="mt-4 inline-block rounded-md bg-field-700 px-5 py-2.5 text-sm font-semibold text-white hover:bg-field-800"
        >
          Go to the Assessment form
        </Link>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
      <h1 className="text-2xl font-bold text-field-900">Assessment results</h1>
      <p className="mt-1 text-sm text-field-600">
        Based on the dates and conditions you supplied. Results come directly from the
        decision engine - nothing here is a hardcoded example.
      </p>

      <div className="mt-6 grid gap-6 lg:grid-cols-2">
        <ScenarioResult assessment={data.baseline} />
        <ScenarioResult assessment={data.alternative} />
      </div>
    </div>
  );
}

function ScenarioResult({ assessment }) {
  if (!assessment) return null;
  const isAlternative = assessment.scenario === "alternative";

  return (
    <section className="rounded-xl border border-field-200 bg-white p-5 shadow-sm">
      <p className="text-xs font-semibold uppercase tracking-wide text-field-500">
        {isAlternative ? "Alternative" : "Baseline"}
      </p>
      <h2 className="mt-1 text-lg font-bold text-field-900">{assessment.scenario_name}</h2>

      <div className="mt-3 flex flex-wrap items-center gap-2">
        <ResultBadge result={assessment.result} />
        <ConfidenceBadge confidence={assessment.evidence_confidence} />
        <ValidationBadge status={assessment.validation_status} />
      </div>

      {assessment.validation_message && (
        <p className="mt-3 rounded-md bg-amber-50 px-3 py-2 text-sm text-amber-700">
          {assessment.validation_message}
        </p>
      )}

      {isAlternative && assessment.calculation?.available_window_days !== undefined && (
        <div className="mt-4">
          <MungbeanWindowBar calculation={assessment.calculation} />
        </div>
      )}

      <Section title="Reasons">
        <BulletList items={assessment.reasons} />
      </Section>

      <Section title="Constraints and risks">
        <BulletList items={assessment.constraints_and_risks} />
      </Section>

      <Section title="Supporting data">
        <SupportingData data={assessment.supporting_data} />
      </Section>

      <Section title="Limitations">
        <BulletList items={assessment.limitations} />
      </Section>
    </section>
  );
}

function Section({ title, children }) {
  return (
    <div className="mt-5">
      <p className="text-sm font-semibold text-field-800">{title}</p>
      <div className="mt-1.5">{children}</div>
    </div>
  );
}

function BulletList({ items }) {
  if (!items || items.length === 0) {
    return <p className="text-sm text-field-500">None reported.</p>;
  }
  return (
    <ul className="list-inside list-disc space-y-1 text-sm text-field-700">
      {items.map((item, i) => (
        <li key={i}>{item}</li>
      ))}
    </ul>
  );
}

function SupportingData({ data }) {
  if (!data) return <p className="text-sm text-field-500">None reported.</p>;
  const { research_sources, climate_context, district_static_context, farm_soil_test } = data;

  return (
    <div className="space-y-3 text-sm text-field-700">
      {climate_context && (
        <div className="rounded-md bg-field-50 px-3 py-2">
          <p className="font-medium text-field-900">
            Historical climate context ({climate_context.period})
          </p>
          <p className="text-xs text-field-500">{climate_context.note}</p>
          <ul className="mt-1.5 space-y-0.5 text-xs">
            {Object.entries(climate_context.statistics || {}).map(([key, stat]) => (
              <li key={key}>
                <span className="font-medium">{stat.label}:</span> mean {stat.mean}, range{" "}
                {stat.min}-{stat.max}
              </li>
            ))}
          </ul>
        </div>
      )}

      {district_static_context && (
        <div className="rounded-md bg-earth-50 px-3 py-2 text-xs">
          <p className="font-medium text-field-900">{district_static_context.scope}</p>
          <p className="mt-1">
            Soil (0-5cm): pH {district_static_context.soil_0_5cm?.ph?.toFixed(2)}, clay{" "}
            {district_static_context.soil_0_5cm?.clay_pct?.toFixed(1)}%, sand{" "}
            {district_static_context.soil_0_5cm?.sand_pct?.toFixed(1)}%
          </p>
          <p>
            Terrain: mean elevation {district_static_context.terrain?.elevation_m_mean?.toFixed(0)} m,
            mean slope {district_static_context.terrain?.slope_degrees_mean?.toFixed(2)}&deg;
          </p>
          <p className="mt-1 text-field-500">{district_static_context.terrain?.caveat}</p>
        </div>
      )}

      {farm_soil_test && (
        <div className="rounded-md bg-field-100 px-3 py-2 text-xs">
          <p className="font-medium text-field-900">Farm-supplied soil test (overrides district context)</p>
          {farm_soil_test.ph && <p>pH: {farm_soil_test.ph}</p>}
          {farm_soil_test.texture_note && <p>Note: {farm_soil_test.texture_note}</p>}
        </div>
      )}

      {research_sources && research_sources.length > 0 && (
        <div>
          <p className="font-medium text-field-900">Research sources used</p>
          <ul className="mt-1 list-inside list-disc space-y-0.5 text-xs">
            {research_sources.map((url) => (
              <li key={url} className="truncate">
                <a href={url} target="_blank" rel="noreferrer" className="text-field-600 underline">
                  {url}
                </a>
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
