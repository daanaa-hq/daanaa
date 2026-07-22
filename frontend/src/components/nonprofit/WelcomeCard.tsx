interface WelcomeCardProps {
  organizationName: string
  onDismiss: () => void
}

export default function WelcomeCard({ organizationName, onDismiss }: WelcomeCardProps) {
  return (
    <div className="bg-gradient-to-r from-soft-gold/20 via-soft-gold/10 to-transparent border-2 border-soft-gold/50 rounded-2xl p-6 mb-6">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h2 className="font-display text-xl text-deep-navy mb-2">Welcome to your dashboard, {organizationName}!</h2>
          <p className="font-body text-[14px] text-cool-grey mb-4 leading-relaxed">
            Here you can manage volunteer hours, update your profile, and see how your organization appears to donors. Start with the attention items below, then explore the quick actions.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mb-4">
            <div className="bg-white rounded-lg p-3 border border-soft-gold/30">
              <div className="text-2xl mb-1">📋</div>
              <p className="font-body text-[12px] font-semibold text-deep-navy mb-1">Profile</p>
              <p className="font-body text-[11px] text-cool-grey">Update how donors see your organization</p>
            </div>
            <div className="bg-white rounded-lg p-3 border border-soft-gold/30">
              <div className="text-2xl mb-1">✓</div>
              <p className="font-body text-[12px] font-semibold text-deep-navy mb-1">Approvals</p>
              <p className="font-body text-[11px] text-cool-grey">Review volunteer hour submissions</p>
            </div>
            <div className="bg-white rounded-lg p-3 border border-soft-gold/30">
              <div className="text-2xl mb-1">📊</div>
              <p className="font-body text-[12px] font-semibold text-deep-navy mb-1">Reporting</p>
              <p className="font-body text-[11px] text-cool-grey">Export data for your board</p>
            </div>
          </div>
        </div>

        <button
          onClick={onDismiss}
          className="ml-4 flex-shrink-0 w-6 h-6 rounded-full hover:bg-soft-gold/20 flex items-center justify-center text-cool-grey hover:text-deep-navy transition"
          aria-label="Dismiss welcome message"
          type="button"
        >
          <span className="text-xl leading-none">×</span>
        </button>
      </div>
    </div>
  )
}
