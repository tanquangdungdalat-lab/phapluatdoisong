"use client";

import { FormEvent, useEffect, useState } from "react";

type VideoStatus = {
  task_id: string;
  state: string;
  progress?: number;
  step?: string;
  error?: string;
  result?: {
    video_url?: string;
    title?: string;
    demo?: boolean;
  };
};

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8005";

export default function VideoGeneratorPage() {
  const [title, setTitle] = useState("");
  const [content, setContent] = useState("");
  const [aspectRatio, setAspectRatio] = useState("16:9");
  const [taskId, setTaskId] = useState<string | null>(null);
  const [statusData, setStatusData] = useState<VideoStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleGenerate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setLoading(true);
    setError(null);
    setStatusData(null);
    setTaskId(null);

    try {
      const response = await fetch(`${API_BASE}/api/v1/videos/generate`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ title, content, aspect_ratio: aspectRatio }),
      });
      if (!response.ok) {
        const body = await response.json().catch(() => null);
        throw new Error(body?.detail?.[0]?.msg || body?.detail || "Không thể tạo tác vụ.");
      }
      const data: { task_id: string } = await response.json();
      setTaskId(data.task_id);
    } catch (requestError) {
      setError(requestError instanceof Error ? requestError.message : "Lỗi kết nối Backend API.");
      setLoading(false);
    }
  }

  useEffect(() => {
    if (!taskId) return;

    let cancelled = false;
    let timeout: ReturnType<typeof setTimeout>;

    const poll = async () => {
      try {
        const response = await fetch(`${API_BASE}/api/v1/videos/status/${taskId}`, {
          cache: "no-store",
        });
        if (!response.ok) throw new Error("Không thể lấy trạng thái tác vụ.");
        const data: VideoStatus = await response.json();
        if (cancelled) return;
        setStatusData(data);

        if (data.state === "SUCCESS" || data.state === "FAILURE" || data.state === "REVOKED") {
          setLoading(false);
          return;
        }
      } catch (pollError) {
        if (!cancelled) {
          setError(pollError instanceof Error ? pollError.message : "Lỗi khi kiểm tra tiến trình.");
          setLoading(false);
        }
        return;
      }
      if (!cancelled) timeout = setTimeout(poll, 2000);
    };

    void poll();
    return () => {
      cancelled = true;
      clearTimeout(timeout);
    };
  }, [taskId]);

  return (
    <main style={{ maxWidth: 720, margin: "40px auto", fontFamily: "sans-serif", padding: "0 20px" }}>
      <h1>AI Video Generator</h1>
      <p>Tạo video tin tức từ tiêu đề và nội dung bài viết.</p>
      <form onSubmit={handleGenerate} style={{ display: "flex", flexDirection: "column", gap: 16 }}>
        <label>
          Tiêu đề bài báo
          <input
            type="text"
            placeholder="Nhập tiêu đề..."
            value={title}
            onChange={(event) => setTitle(event.target.value)}
            required
            maxLength={200}
            style={{ display: "block", width: "100%", boxSizing: "border-box", padding: 10, marginTop: 6 }}
          />
        </label>
        <label>
          Nội dung hoặc kịch bản
          <textarea
            rows={7}
            placeholder="Dán nội dung tóm tắt hoặc kịch bản tin tức..."
            value={content}
            onChange={(event) => setContent(event.target.value)}
            required
            maxLength={20000}
            style={{ display: "block", width: "100%", boxSizing: "border-box", padding: 10, marginTop: 6 }}
          />
        </label>
        <label>
          Tỉ lệ khung hình
          <select value={aspectRatio} onChange={(event) => setAspectRatio(event.target.value)} style={{ display: "block", padding: 10, marginTop: 6 }}>
            <option value="16:9">16:9 (YouTube / Website)</option>
            <option value="9:16">9:16 (Shorts / Reels)</option>
          </select>
        </label>
        <button type="submit" disabled={loading} style={{ padding: 12, fontSize: 16, cursor: loading ? "wait" : "pointer" }}>
          {loading ? "Đang xử lý..." : "Tạo video"}
        </button>
      </form>

      {error && <p role="alert" style={{ color: "#b00020" }}>{error}</p>}
      {taskId && <p>Mã tác vụ: <code>{taskId}</code></p>}
      {statusData && (
        <section aria-live="polite" style={{ marginTop: 24, padding: 16, border: "1px solid #ddd", borderRadius: 8 }}>
          <p><strong>Trạng thái:</strong> {statusData.state}</p>
          {statusData.step && <p>{statusData.step} ({statusData.progress ?? 0}%)</p>}
          {statusData.state === "PROCESSING" && (
            <progress value={statusData.progress ?? 0} max={100} style={{ width: "100%" }} />
          )}
          {statusData.error && <p role="alert" style={{ color: "#b00020" }}>{statusData.error}</p>}
          {statusData.result?.video_url && (
            <div style={{ marginTop: 16 }}>
              {statusData.result.demo && <p>Đây là video mẫu; chưa được tạo từ nội dung đã nhập.</p>}
              <video src={statusData.result.video_url} controls style={{ width: "100%", borderRadius: 8 }} />
            </div>
          )}
        </section>
      )}
    </main>
  );
}
