"use client";

import { useTheme } from "next-themes@0.4.6";
import { Toaster as Sonner, ToasterProps } from "sonner@2.0.3";

const Toaster = ({ ...props }: ToasterProps) => {
  return (
    <Sonner
      theme="dark"
      className="toaster group"
      style={
        {
          "--normal-bg": "#1f2937",
          "--normal-text": "#f3f4f6",
          "--normal-border": "#374151",
          "--success-bg": "#052e16",
          "--success-text": "#4ade80",
          "--success-border": "#166534",
          "--error-bg": "#450a0a",
          "--error-text": "#f87171",
          "--error-border": "#7f1d1d",
          "--info-bg": "#1e3a5f",
          "--info-text": "#60a5fa",
          "--info-border": "#1e40af",
        } as React.CSSProperties
      }
      {...props}
    />
  );
};

export { Toaster };
