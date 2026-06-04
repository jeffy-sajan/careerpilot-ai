/**
 * Gemini Direct Client
 *
 * Calls the Google Generative AI REST API directly from the browser
 * using the user's own API key. The key never touches our backend.
 */

const GEMINI_API_BASE =
  "https://generativelanguage.googleapis.com/v1beta/models";

export interface GeminiSuggestion {
  section: string;
  original_text: string;
  suggested_text: string;
  reasoning: string;
  optimization_type: string;
}

interface GeminiResponse {
  candidates?: Array<{
    content?: {
      parts?: Array<{
        text?: string;
      }>;
    };
    finishReason?: string;
  }>;
  error?: {
    code: number;
    message: string;
    status: string;
  };
}

/**
 * Calls Gemini generateContent directly from the browser.
 *
 * @param apiKey   The user's personal Gemini API key (from localStorage)
 * @param model    Model name, e.g. "gemini-2.5-flash"
 * @param prompt   The assembled prompt string (fetched from our backend)
 * @param schema   JSON schema to enforce structured output
 */
export async function callGeminiDirect(
  apiKey: string,
  model: string,
  prompt: string,
  schema: Record<string, unknown>,
): Promise<GeminiSuggestion[]> {
  const url = `${GEMINI_API_BASE}/${model}:generateContent?key=${apiKey}`;

  const body = {
    contents: [
      {
        parts: [{ text: prompt }],
      },
    ],
    generationConfig: {
      responseMimeType: "application/json",
      responseSchema: schema,
      temperature: 0.7,
    },
  };

  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const err = (await res.json().catch(() => ({}))) as GeminiResponse;
    const code = err.error?.code ?? res.status;

    if (code === 400) {
      throw new Error(
        "Invalid API key. Please check your Gemini API key and try again.",
      );
    }
    if (code === 403) {
      throw new Error(
        "API key does not have permission to access the Gemini API. Please check your key.",
      );
    }
    if (code === 429) {
      throw new Error(
        "Your personal API key has exceeded its rate limit. Please wait a moment and try again.",
      );
    }
    if (code === 503) {
      throw new Error(
        "Gemini API is temporarily unavailable. Please try again in a few moments.",
      );
    }

    throw new Error(
      err.error?.message ?? `Gemini API request failed (${res.status})`,
    );
  }

  const data = (await res.json()) as GeminiResponse;

  const text = data.candidates?.[0]?.content?.parts?.[0]?.text;
  if (!text) {
    throw new Error("Gemini returned an empty response. Please try again.");
  }

  const parsed = JSON.parse(text) as { suggestions?: GeminiSuggestion[] };
  return parsed.suggestions ?? [];
}
