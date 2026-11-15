import { useEffect, useMemo, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { getClimate, ApiError } from "../api";
import { LoadingState, ErrorState } from "../components/Status";

const MONTH_LABELS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];

export default function Climate() {
  const [payload, setPayload] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showDetailed, setShowDetailed] = useState(false);
  const [showNdvi, setShowNdvi] = useState(false);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      const result = await getClimate({ detail: true });
      setPayload(result);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load climate data.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  const seasonal = useMemo(() => {
    if (!payload?.detailed_monthly) return [];
    const byMonth = {};
    for (const row of payload.detailed_monthly) {
      const m = row.month_of_year;
      byMonth[m] = byMonth[m] || { count: 0, imerg: 0, power: 0, t2m: 0, lst: 0, ndvi: 0 };
      byMonth[m].count += 1;
      byMonth[m].imerg += row.imerg_rainfall_mm || 0;
      byMonth[m].power += row.power_prectotcorr || 0;
      byMonth[m].t2m += row.power_t2m || 0;
      byMonth[m].lst += row.lst_mean_lst_c || 0;
      byMonth[m].ndvi += row.ndvi_mean_ndvi || 0;
    }
    return Array.from({ length: 12 }, (_, i) => {
      const m = i + 1;
      const b = byMonth[m];
      if (!b) return { month: MONTH_LABELS[i] };
      return {
        month: MONTH_LABELS[i],
        imerg_rainfall_mm: round(b.imerg / b.count),
        power_prectotcorr: round(b.power / b.count),
        power_t2m: round(b.t2m / b.count),
        lst_mean_lst_c: round(b.lst / b.count),
        ndvi_mean_ndvi: round(b.ndvi / b.count, 3),
      };
    });
  }, [payload]);

  const detailed = useMemo(() => {
    if (!payload?.detailed_monthly) return [];
    return payload.detailed_monthly.map((row) => ({ ...row, label: row.month.slice(0, 7) }));
  }, [payload]);

  const chartData = showDetailed ? detailed : seasonal;
  const xKey = showDetailed ? "label" : "month";

  if (loading) {
    return (
      <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
        <LoadingState label="Loading historical climate data..." />
      </div>
    );
  }
  if (error) {
    return (
      <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
        <ErrorState message={error} onRetry={load} />
      </div>
    );
  }

  const summary = payload?.summary;

  return (
    <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6">
      <h1 className="text-2xl font-bold text-field-900">Historical climate context</h1>
      <p className="mt-1 text-sm text-field-700">
        Period: <strong>{summary?.period || "2016-2025"}</strong>. These are historical
        observations only - never a forecast for an upcoming season, and never a
        farm-level measurement.
      </p>

      {summary && (
        <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {Object.entries(summary.statistics)
            .filter(([key]) => showNdvi || key !== "ndvi_mean_ndvi")
            .map(([key, stat]) => (
              <div key={key} className="rounded-lg border border-field-200 bg-white p-4">
                <p className="text-xs font-medium text-field-500">{stat.label}</p>
                <p className="mt-1 text-xl font-bold text-field-900">{stat.mean}</p>
                <p className="text-xs text-field-500">
                  range {stat.min} - {stat.max}
                </p>
              </div>
            ))}
        </div>
      )}

      <div className="mt-6 flex flex-wrap items-center gap-4 rounded-lg border border-field-200 bg-white px-4 py-3 text-sm">
        <label className="flex items-center gap-2">
          <input type="checkbox" checked={showDetailed} onChange={(e) => setShowDetailed(e.target.checked)} />
          Show detailed monthly data (2016-2025, 120 months) instead of the seasonal average
        </label>
        <label className="flex items-center gap-2">
          <input type="checkbox" checked={showNdvi} onChange={(e) => setShowNdvi(e.target.checked)} />
          Include NDVI (optional vegetation-greenness context)
        </label>
      </div>

      <ChartCard title="Monthly rainfall - IMERG vs NASA POWER (comparison)">
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2ecdd" />
          <XAxis dataKey={xKey} tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} label={{ value: "mm", angle: -90, position: "insideLeft", fontSize: 11 }} />
          <Tooltip />
          <Legend />
          <Line type="monotone" dataKey="imerg_rainfall_mm" name="IMERG rainfall (mm)" stroke="#386830" dot={false} />
          <Line type="monotone" dataKey="power_prectotcorr" name="POWER precipitation (mm)" stroke="#a07f45" dot={false} strokeDasharray="4 2" />
        </LineChart>
      </ChartCard>

      <ChartCard title="Mean air temperature - NASA POWER">
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2ecdd" />
          <XAxis dataKey={xKey} tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} label={{ value: "deg C", angle: -90, position: "insideLeft", fontSize: 11 }} />
          <Tooltip />
          <Line type="monotone" dataKey="power_t2m" name="Mean air temperature (deg C)" stroke="#2c5326" dot={false} />
        </LineChart>
      </ChartCard>

      <ChartCard title="Land-surface temperature - MODIS (not air temperature)">
        <LineChart data={chartData}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e2ecdd" />
          <XAxis dataKey={xKey} tick={{ fontSize: 11 }} />
          <YAxis tick={{ fontSize: 11 }} label={{ value: "deg C", angle: -90, position: "insideLeft", fontSize: 11 }} />
          <Tooltip />
          <Line type="monotone" dataKey="lst_mean_lst_c" name="Land-surface temperature (deg C)" stroke="#bc9a5a" dot={false} />
        </LineChart>
      </ChartCard>

      {showNdvi && (
        <ChartCard title="NDVI - optional vegetation-greenness context (not crop identification)">
          <LineChart data={chartData}>
            <CartesianGrid strokeDasharray="3 3" stroke="#e2ecdd" />
            <XAxis dataKey={xKey} tick={{ fontSize: 11 }} />
            <YAxis domain={[0, 1]} tick={{ fontSize: 11 }} />
            <Tooltip />
            <Line type="monotone" dataKey="ndvi_mean_ndvi" name="Mean NDVI" stroke="#72a160" dot={false} />
          </LineChart>
        </ChartCard>
      )}
    </div>
  );
}

function ChartCard({ title, children }) {
  return (
    <div className="mt-6 rounded-xl border border-field-200 bg-white p-4">
      <p className="mb-2 text-sm font-semibold text-field-900">{title}</p>
      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          {children}
        </ResponsiveContainer>
      </div>
    </div>
  );
}

function round(value, digits = 1) {
  const factor = 10 ** digits;
  return Math.round(value * factor) / factor;
}
