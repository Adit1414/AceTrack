import React from "react";

export function Select({ children, onValueChange, defaultValue, ...props }) {
  return (
    <select
      className="border rounded px-2 py-1"
      defaultValue={defaultValue}
      onChange={e => onValueChange && onValueChange(e.target.value)}
      {...props}
    >
      {children}
    </select>
  );
}

export function SelectTrigger({ children, ...props }) {
  return <div {...props}>{children}</div>;
}
export function SelectValue({ placeholder }) {
  return <option disabled value="">{placeholder}</option>;
}
export function SelectContent({ children }) {
  return <>{children}</>;
}
export function SelectItem({ value, children, disabled }) {
  return (
    <option value={value} disabled={disabled}>
      {children}
    </option>
  );
}