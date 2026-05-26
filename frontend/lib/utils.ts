import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatEnum(value: string): string {
  return value
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase())
    .replace(/\bNc\b/g, "NC")
    .replace(/\bOfi\b/g, "OFI")
}

// --- Shared error constants for action responses ---
export const ACTION_ERROR = {
  UNAUTHORIZED: "unauthorized",
  VALIDATION: "validation",
  NOT_FOUND: "not_found",
  CONFLICT: "conflict",
  UNKNOWN: "unknown"
} as const
