import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "AI Video Generator",
  description: "Tạo video tin tức từ nội dung bài viết.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="vi">
      <body>{children}</body>
    </html>
  );
}
