import { useEffect, useState, type ReactNode } from "react";
import "./Toast.css";

export type ToastTone = "info" | "success" | "danger";

export interface ToastMessage {
  id: number;
  text: string;
  tone: ToastTone;
}

let _id = 0;

export function pushToast(
  setToasts: (fn: (prev: ToastMessage[]) => ToastMessage[]) => void,
  text: string,
  tone: ToastTone = "info"
) {
  setToasts((prev) => [...prev, { id: ++_id, text, tone }]);
}

export function ToastViewport({ children }: { children?: ReactNode }) {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  useEffect(() => {
    const onPush = (e: Event) => {
      const ce = e as CustomEvent<{ text: string; tone?: ToastTone }>;
      pushToast(setToasts, ce.detail.text, ce.detail.tone ?? "info");
    };
    window.addEventListener("wa:toast", onPush as EventListener);
    return () => window.removeEventListener("wa:toast", onPush as EventListener);
  }, []);

  useEffect(() => {
    if (toasts.length === 0) return;
    const last = toasts[toasts.length - 1];
    const t = setTimeout(() => {
      setToasts((prev) => prev.filter((m) => m.id !== last.id));
    }, 4000);
    return () => clearTimeout(t);
  }, [toasts]);

  return (
    <div className="wa-toast-viewport" aria-live="polite" aria-atomic="false">
      {children}
      {toasts.map((t) => (
        <div key={t.id} className={`wa-toast wa-toast--${t.tone}`} role="status">
          {t.text}
        </div>
      ))}
    </div>
  );
}

export function toast(text: string, tone: ToastTone = "info") {
  window.dispatchEvent(new CustomEvent("wa:toast", { detail: { text, tone } }));
}
