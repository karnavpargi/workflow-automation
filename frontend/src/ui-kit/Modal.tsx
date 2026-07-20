import { useEffect, useRef, type ReactNode } from "react";
import "./Modal.css";

export interface ModalProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: ReactNode;
  footer?: ReactNode;
}

export function Modal({ open, onClose, title, children, footer }: ModalProps) {
  const dialogRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    document.addEventListener("keydown", onKey);
    dialogRef.current?.focus();
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;
  return (
    <div
      className="wa-modal__backdrop"
      onClick={onClose}
      role="presentation"
    >
      <div
        ref={dialogRef}
        className="wa-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="wa-modal-title"
        tabIndex={-1}
        onClick={(e) => e.stopPropagation()}
      >
        <h2 id="wa-modal-title" className="wa-modal__title">
          {title}
        </h2>
        <div className="wa-modal__body">{children}</div>
        {footer && <div className="wa-modal__footer">{footer}</div>}
      </div>
    </div>
  );
}
