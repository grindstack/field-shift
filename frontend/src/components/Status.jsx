export function LoadingState({ label = "Loading..." }) {
  return (
    <div className="flex items-center gap-3 rounded-lg border border-field-200 bg-white px-4 py-6 text-field-600">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-field-300 border-t-field-700" />
      <span>{label}</span>
    </div>
  );
}

export function ErrorState({ message, onRetry }) {
  return (
    <div className="rounded-lg border border-rose-200 bg-rose-50 px-4 py-4 text-rose-700">
      <p className="font-semibold">Something went wrong</p>
      <p className="mt-1 text-sm">{message}</p>
      {onRetry && (
        <button
          onClick={onRetry}
          className="mt-3 rounded-md border border-rose-300 bg-white px-3 py-1.5 text-sm font-medium text-rose-700 hover:bg-rose-100"
        >
          Try again
        </button>
      )}
    </div>
  );
}
