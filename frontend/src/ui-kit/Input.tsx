import { forwardRef, type InputHTMLAttributes } from "react";
import "./Input.css";

export interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, id, className, ...rest }, ref) => {
    const inputId = id ?? `input-${label.replace(/\s+/g, "-").toLowerCase()}`;
    const errId = error ? `${inputId}-error` : undefined;
    return (
      <div className="wa-field">
        <label className="wa-field__label" htmlFor={inputId}>
          {label}
        </label>
        <input
          ref={ref}
          id={inputId}
          className={["wa-input", className].filter(Boolean).join(" ")}
          aria-invalid={error ? true : undefined}
          aria-describedby={errId}
          {...rest}
        />
        {error && (
          <span id={errId} className="wa-field__error" role="alert">
            {error}
          </span>
        )}
      </div>
    );
  }
);
Input.displayName = "Input";
