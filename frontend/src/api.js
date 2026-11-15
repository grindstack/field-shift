const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:5000";

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

async function request(path, options = {}) {
  let response;
  try {
    response = await fetch(`${API_BASE}${path}`, {
      headers: { "Content-Type": "application/json" },
      ...options,
    });
  } catch {
    throw new ApiError(
      "Could not reach the Field Shift backend. Is the Flask server running on " +
        API_BASE +
        "?",
      0
    );
  }

  let body = null;
  try {
    body = await response.json();
  } catch {
    // non-JSON response body is handled below via response.ok
  }

  if (!response.ok) {
    const message = body?.error || `Request failed with status ${response.status}.`;
    throw new ApiError(message, response.status);
  }
  return body;
}

export function getHealth() {
  return request("/api/health");
}

export function getClimate({ months, detail } = {}) {
  const params = new URLSearchParams();
  if (months && months.length) params.set("months", months.join(","));
  if (detail) params.set("detail", "true");
  const qs = params.toString();
  return request(`/api/climate${qs ? `?${qs}` : ""}`);
}

export function postAssess(payload) {
  return request("/api/assess", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export { ApiError };
