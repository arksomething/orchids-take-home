"use client";

import { useState, useRef, useEffect } from "react";

export default function Home() {
  const [url, setUrl] = useState("https://example.com/");
  const [response, setResponse] = useState("");
  const [processedResponse, setProcessedResponse] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [copied, setCopied] = useState(false);
  const iframeRef = useRef<HTMLIFrameElement>(null);
  const responseBuffer = useRef("");

  // Optimize iframe content updates
  useEffect(() => {
    if (!response || !iframeRef.current) return;

    // Process the response to remove markdown markers
    let processed = response;
    if (response.startsWith("```html")) {
      processed = response.slice(7); // Remove ```html
    }
    if (processed.endsWith("```")) {
      processed = processed.slice(0, -3); // Remove ```
    }
    setProcessedResponse(processed);

    const iframe = iframeRef.current;
    const doc = iframe.contentDocument || iframe.contentWindow?.document;
    if (!doc) return;

    // Only update if we have a complete HTML structure
    if (processed.includes("</html>")) {
      doc.open();
      doc.write(`
        <!DOCTYPE html>
        <html>
          <head>
            <base target="_blank">
            <style>
              body { margin: 0; padding: 0; }
              img { max-width: 100%; height: auto; }
            </style>
          </head>
          <body>${processed}</body>
        </html>
      `);
      doc.close();
    }
  }, [response]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (loading) return;

    setLoading(true);
    setError("");
    setResponse("");
    responseBuffer.current = "";

    try {
      const res = await fetch("http://localhost:8000/stream", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ url }),
      });

      if (!res.ok) {
        const errorText = await res.text();
        throw new Error(`Failed to get response: ${errorText}`);
      }

      const reader = res.body?.getReader();
      if (!reader) {
        throw new Error("No reader available");
      }

      const decoder = new TextDecoder();
      let buffer = "";

      try {
        while (true) {
          const { value, done } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value, { stream: true });
          buffer += chunk;
          responseBuffer.current += chunk;

          // Update state with accumulated content
          setResponse(responseBuffer.current);
        }
      } finally {
        reader.releaseLock();
      }
    } catch (err) {
      console.error("Error:", err);
      setError(err instanceof Error ? err.message : "An error occurred");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen p-8">
      <main className="max-w-6xl mx-auto">
        <h1 className="text-2xl font-bold mb-8">Website Replicator</h1>

        <form onSubmit={handleSubmit} className="mb-8">
          <div className="flex gap-4">
            <input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="Enter website URL"
              className="flex-1 px-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-gray-300"
              required
            />
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2 bg-black text-white rounded-lg hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? "Processing..." : "Replicate"}
            </button>
          </div>
        </form>

        {/* Animated loading spinner */}
        {loading && !response && (
          <div className="flex justify-center items-center py-12">
            <div className="flex space-x-2">
              <span className="block w-3 h-3 bg-black rounded-full animate-bounce [animation-delay:-0.32s]"></span>
              <span className="block w-3 h-3 bg-black rounded-full animate-bounce [animation-delay:-0.16s]"></span>
              <span className="block w-3 h-3 bg-black rounded-full animate-bounce"></span>
            </div>
          </div>
        )}

        {error && (
          <div className="p-4 mb-4 text-red-700 bg-red-100 rounded-lg">
            {error}
          </div>
        )}

        {response && (
          <div className="flex flex-col gap-8">
            {/* Generated HTML Box */}
            <div className="rounded-2xl bg-gray-50 border border-gray-200 p-4 font-sans">
              <div className="flex justify-between items-center mb-4 gap-2">
                <span className="text-xs text-black font-sans">html</span>
                <button
                  onClick={async () => {
                    await navigator.clipboard.writeText(response);
                    setCopied(true);
                    setTimeout(() => setCopied(false), 1500);
                  }}
                  className={`flex items-center gap-1 text-xs px-4 py-1 rounded transition-all duration-300 font-sans
                    ${
                      copied
                        ? "bg-green-400 text-white scale-110 animate-pulse"
                        : "bg-gray-200 hover:bg-gray-300"
                    }
                  `}
                >
                  {copied ? "Copied!" : "Copy"}
                </button>
              </div>
              <pre className="whitespace-pre-wrap bg-white rounded-xl p-4 overflow-auto text-sm font-mono max-h-[300px] border border-gray-200">
                {processedResponse}
              </pre>
            </div>

            {/* Preview Box */}
            <div className="rounded-2xl bg-gray-50 border border-gray-200 p-4 font-sans">
              <div className="flex items-center mb-4">
                <span className="text-xs text-black font-sans">preview</span>
              </div>
              <div className="border border-gray-200 rounded-xl overflow-hidden bg-white">
                <iframe
                  ref={iframeRef}
                  className="w-full h-[600px]"
                  sandbox="allow-same-origin allow-scripts"
                  title="Generated HTML Preview"
                />
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
