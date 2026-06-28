const API_BASE = "/api";

export async function recommendMusic(payload) {
  return request("/recommend", payload);
}

export async function nextRecommendation(sessionId, payload) {
  return request(`/recommend/${sessionId}/next`, payload);
}

export async function submitFeedback(payload) {
  return request("/feedback", payload);
}

async function request(path, payload) {
  const response = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  return await response.json();
}
