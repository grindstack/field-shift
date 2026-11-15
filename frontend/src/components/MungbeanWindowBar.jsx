export default function MungbeanWindowBar({ calculation }) {
  if (!calculation || calculation.available_window_days === undefined) return null;

  const {
    available_window_days: available,
    required_minimum_days: minDays,
    required_with_buffer_days: bufferedDays,
    mungbean_duration_range_days: durationRange,
    safety_buffer_days: buffer,
  } = calculation;

  const scaleMax = Math.max(available, bufferedDays) * 1.15;
  const pct = (value) => `${Math.min(100, (value / scaleMax) * 100)}%`;

  return (
    <div className="rounded-lg border border-field-200 bg-white p-4">
      <p className="mb-3 text-sm font-semibold text-field-900">
        Mungbean fallow-window calendar check
      </p>

      <div className="relative h-8 w-full overflow-hidden rounded-md bg-rose-100">
        <div
          className="absolute inset-y-0 left-0 bg-amber-200"
          style={{ left: pct(minDays), width: `calc(${pct(bufferedDays)} - ${pct(minDays)})` }}
        />
        <div
          className="absolute inset-y-0 bg-field-200"
          style={{ left: pct(bufferedDays), right: 0 }}
        />
        {/* available-window marker */}
        <div
          className="absolute inset-y-0 w-0.5 bg-field-900"
          style={{ left: pct(available) }}
        />
        <div
          className="absolute -top-5 -translate-x-1/2 text-[11px] font-semibold text-field-900"
          style={{ left: pct(available) }}
        >
          {available}d
        </div>
      </div>

      <div className="mt-2 flex justify-between text-[11px] text-field-600">
        <span>0 (no window)</span>
        <span>{minDays}d min</span>
        <span>{bufferedDays}d buffered</span>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3 text-xs sm:grid-cols-4">
        <Stat label="Available window" value={`${available} days`} />
        <Stat label="KSK trial duration" value={`${durationRange[0]}-${durationRange[1]} days`} />
        <Stat label="Minimum required" value={`${minDays} days`} />
        <Stat label="Buffered requirement" value={`${bufferedDays} days (+${buffer}d buffer)`} />
      </div>

      <div className="mt-3 flex flex-wrap gap-3 text-[11px] text-field-600">
        <LegendDot className="bg-rose-200" label="Below minimum (insufficient)" />
        <LegendDot className="bg-amber-200" label="Above minimum, below buffer (uncertain)" />
        <LegendDot className="bg-field-200" label="Clears buffer (sufficient)" />
      </div>
    </div>
  );
}

function Stat({ label, value }) {
  return (
    <div className="rounded-md bg-field-50 px-2.5 py-2">
      <p className="text-[10px] uppercase tracking-wide text-field-500">{label}</p>
      <p className="font-semibold text-field-900">{value}</p>
    </div>
  );
}

function LegendDot({ className, label }) {
  return (
    <span className="inline-flex items-center gap-1.5">
      <span className={`h-2.5 w-2.5 rounded-full ${className}`} />
      {label}
    </span>
  );
}
