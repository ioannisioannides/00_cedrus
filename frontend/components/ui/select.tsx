/**
 * Accessible native-select implementation matching the shadcn/ui Select API.
 *
 * Strategy: Select extracts options from children synchronously via tree
 * traversal. SelectTrigger renders a styled div with an invisible native
 * <select> overlay — the browser handles all native interaction (click, keyboard,
 * mobile). SelectContent/SelectItem are markers that render nothing themselves.
 */
"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { ChevronDown } from "lucide-react"

// ── Item shape ─────────────────────────────────────────────────────────────

interface OptionDef {
  value: string
  label: string
  disabled?: boolean
}

// ── Context ────────────────────────────────────────────────────────────────

interface SelectCtx {
  value: string
  onChange: (v: string) => void
  name?: string
  required?: boolean
  disabled?: boolean
  options: OptionDef[]
}

const SelectContext = React.createContext<SelectCtx>({
  value: "",
  onChange: () => {},
  options: [],
})

// ── Child traversal to extract options ─────────────────────────────────────

function extractOptions(children: React.ReactNode): OptionDef[] {
  const opts: OptionDef[] = []
  React.Children.forEach(children, (child) => {
    if (!React.isValidElement(child)) return
    const type = child.type as React.FC & { displayName?: string }
    if (type === SelectItem || type.displayName === "SelectItem") {
      const p = child.props as { value: string; children: React.ReactNode; disabled?: boolean }
      opts.push({ value: p.value, label: String(p.children), disabled: p.disabled })
      return
    }
    const p = child.props as { children?: React.ReactNode }
    if (p.children) opts.push(...extractOptions(p.children))
  })
  return opts
}

// ── Select (root) ──────────────────────────────────────────────────────────

interface SelectProps {
  value?: string
  defaultValue?: string
  onValueChange?: (v: string) => void
  name?: string
  required?: boolean
  disabled?: boolean
  children: React.ReactNode
}

function Select({
  value: controlledValue,
  defaultValue = "",
  onValueChange,
  name,
  required,
  disabled,
  children,
}: SelectProps) {
  const [internal, setInternal] = React.useState(defaultValue)
  const isControlled = controlledValue !== undefined
  const value = isControlled ? controlledValue! : internal

  const options = extractOptions(children)

  const onChange = React.useCallback(
    (v: string) => {
      if (!isControlled) setInternal(v)
      onValueChange?.(v)
    },
    [isControlled, onValueChange]
  )

  return (
    <SelectContext.Provider value={{ value, onChange, name, required, disabled, options }}>
      {children}
    </SelectContext.Provider>
  )
}

// ── SelectTrigger ──────────────────────────────────────────────────────────

interface SelectTriggerProps {
  id?: string
  className?: string
  children?: React.ReactNode
}

function SelectTrigger({ id, className, children }: SelectTriggerProps) {
  const { value, onChange, name, required, disabled, options } = React.useContext(SelectContext)

  return (
    <div
      data-slot="select-trigger"
      className={cn(
        "relative flex h-8 w-full items-center justify-between gap-2 rounded-lg border border-input bg-transparent px-2.5 py-1 text-sm transition-colors outline-none",
        "focus-within:border-ring focus-within:ring-3 focus-within:ring-ring/50",
        disabled && "pointer-events-none opacity-50",
        className
      )}
    >
      {children}
      <ChevronDown className="h-4 w-4 shrink-0 opacity-50 pointer-events-none" />
      {/* Invisible native select — handles all browser interaction */}
      <select
        id={id}
        name={name}
        value={value}
        required={required}
        disabled={disabled}
        onChange={(e) => onChange(e.target.value)}
        className="absolute inset-0 h-full w-full cursor-pointer opacity-0"
      >
        {!value && <option value="" disabled />}
        {options.map((o) => (
          <option key={o.value} value={o.value} disabled={o.disabled}>
            {o.label}
          </option>
        ))}
      </select>
    </div>
  )
}

// ── SelectValue ────────────────────────────────────────────────────────────

function SelectValue({ placeholder }: { placeholder?: string }) {
  const { value, options } = React.useContext(SelectContext)
  const label = options.find((o) => o.value === value)?.label
  return (
    <span className="truncate">
      {label ?? <span className="text-muted-foreground">{placeholder}</span>}
    </span>
  )
}

// ── SelectContent — marker only, renders children for extraction ───────────

function SelectContent({ children }: { children?: React.ReactNode }) {
  return <>{children}</>
}

// ── SelectItem — renders nothing; extracted by Select ─────────────────────

/* eslint-disable-next-line @typescript-eslint/no-unused-vars */
function SelectItem(props: {
  value: string
  children: React.ReactNode
  disabled?: boolean
  className?: string
}) {
  return null
}
SelectItem.displayName = "SelectItem"

// ── Stubs for API completeness ─────────────────────────────────────────────

function SelectLabel({ children, className }: { children?: React.ReactNode; className?: string }) {
  return <div className={cn("px-2 py-1 text-xs font-semibold text-muted-foreground", className)}>{children}</div>
}

function SelectSeparator({ className }: { className?: string }) {
  return <div className={cn("my-1 h-px bg-muted", className)} />
}

export {
  Select,
  SelectContent,
  SelectItem,
  SelectLabel,
  SelectSeparator,
  SelectTrigger,
  SelectValue,
}

