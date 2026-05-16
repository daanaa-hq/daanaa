interface MistakeRegistryProps {
  compact?: boolean
}

export default function MistakeRegistry({ compact = false }: MistakeRegistryProps) {
  const monitorIcon = (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#9CA3AF" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <circle cx="12" cy="12" r="3"/>
      <path d="M2 12h2M20 12h2M12 2v2M12 20v2M5.64 5.64l1.41 1.41M15.54 15.54l1.41 1.41M5.64 18.36l1.41-1.41M15.54 8.46l1.41-1.41"/>
    </svg>
  )

  if (compact) {
    return (
      <div className="flex items-center gap-3">
        <div className="w-8 h-8 rounded-full bg-cool-grey/10 flex items-center justify-center shrink-0">
          {monitorIcon}
        </div>
        <div>
          <p className="font-body text-[13px] font-semibold text-deep-navy">Mistake Registry</p>
          <p className="font-body text-[12px] text-cool-grey">Monitoring active · No incidents on file</p>
        </div>
      </div>
    )
  }

  return (
    <div className="border-t border-light-grey pt-4">
      <div className="flex items-center gap-2 mb-2">
        {monitorIcon}
        <p className="font-body text-[10px] font-semibold tracking-[0.07em] text-cool-grey uppercase">
          Mistake Registry
        </p>
      </div>
      <div className="flex items-start gap-2">
        <span className="inline-block w-2 h-2 rounded-full bg-cool-grey/30 shrink-0 mt-[5px]" />
        <p className="font-body text-[12px] text-cool-grey leading-[1.45]">
          Monitoring active — no incidents on file for this organization.
        </p>
      </div>
      <p className="mt-2 font-body text-[11px] text-cool-grey/55 leading-[1.35]">
        MERIT flags known incidents of financial misconduct or misleading donor communications. Absence of incidents reflects current data availability, not a clean bill of health.
      </p>
    </div>
  )
}
