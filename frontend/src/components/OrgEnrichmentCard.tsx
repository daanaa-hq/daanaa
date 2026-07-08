import React from 'react'

interface ContactData {
  email?: string
  phone?: string
  street_address?: string
  executive_name?: string
  board_size?: number
  contact_verified_date?: string
  contact_sources?: string[]
}

interface ProgramsData {
  program_descriptions?: string[]
  service_area?: string
  years_active?: number
  accreditations?: string[]
  programs_verified_date?: string
  program_sources?: string[]
}

interface OrgEnrichmentCardProps {
  contact?: ContactData | null
  programs?: ProgramsData | null
  loading?: boolean
}

export default function OrgEnrichmentCard({ contact, programs, loading }: OrgEnrichmentCardProps) {
  if (!contact && !programs && !loading) {
    return null
  }

  return (
    <div className="space-y-6 mt-8 pt-6 border-t border-light-grey/40">
      {/* Contact Card */}
      {contact && Object.keys(contact).filter(k => k !== 'contact_verified_date' && k !== 'contact_sources').length > 0 && (
        <div className="space-y-3">
          <h3 className="font-body text-[14px] font-semibold text-deep-navy uppercase tracking-[0.08em]">
            Contact Information
          </h3>
          <div className="space-y-2">
            {contact.email && (
              <div className="flex items-start gap-3">
                <span className="text-[16px]">📧</span>
                <div>
                  <p className="font-body text-[12px] text-cool-grey uppercase tracking-[0.05em]">Email</p>
                  <a href={`mailto:${contact.email}`} className="font-body text-[13px] text-link-gold hover:text-bright-gold break-all">
                    {contact.email}
                  </a>
                </div>
              </div>
            )}
            {contact.phone && (
              <div className="flex items-start gap-3">
                <span className="text-[16px]">📞</span>
                <div>
                  <p className="font-body text-[12px] text-cool-grey uppercase tracking-[0.05em]">Phone</p>
                  <a href={`tel:${contact.phone}`} className="font-body text-[13px] text-link-gold hover:text-bright-gold">
                    {contact.phone}
                  </a>
                </div>
              </div>
            )}
            {contact.executive_name && (
              <div className="flex items-start gap-3">
                <span className="text-[16px]">👤</span>
                <div>
                  <p className="font-body text-[12px] text-cool-grey uppercase tracking-[0.05em]">Executive</p>
                  <p className="font-body text-[13px] text-deep-navy">{contact.executive_name}</p>
                </div>
              </div>
            )}
            {contact.board_size && (
              <div className="flex items-start gap-3">
                <span className="text-[16px]">👥</span>
                <div>
                  <p className="font-body text-[12px] text-cool-grey uppercase tracking-[0.05em]">Board Members</p>
                  <p className="font-body text-[13px] text-deep-navy">{contact.board_size} members</p>
                </div>
              </div>
            )}
            {contact.street_address && (
              <div className="flex items-start gap-3">
                <span className="text-[16px]">📍</span>
                <div>
                  <p className="font-body text-[12px] text-cool-grey uppercase tracking-[0.05em]">Address</p>
                  <p className="font-body text-[13px] text-deep-navy">{contact.street_address}</p>
                </div>
              </div>
            )}
          </div>
          {contact.contact_verified_date && (
            <p className="font-body text-[11px] text-cool-grey/60 mt-2">
              Last verified: {new Date(contact.contact_verified_date).toLocaleDateString()}
            </p>
          )}
        </div>
      )}

      {/* Programs Card */}
      {programs && Object.keys(programs).filter(k => k !== 'programs_verified_date' && k !== 'program_sources').length > 0 && (
        <div className="space-y-3">
          <h3 className="font-body text-[14px] font-semibold text-deep-navy uppercase tracking-[0.08em]">
            Organization Profile
          </h3>
          <div className="space-y-2">
            {programs.years_active !== undefined && (
              <div className="flex items-start gap-3">
                <span className="text-[16px]">📅</span>
                <div>
                  <p className="font-body text-[12px] text-cool-grey uppercase tracking-[0.05em]">Years Active</p>
                  <p className="font-body text-[13px] text-deep-navy">{programs.years_active} years</p>
                </div>
              </div>
            )}
            {programs.service_area && (
              <div className="flex items-start gap-3">
                <span className="text-[16px]">🗺️</span>
                <div>
                  <p className="font-body text-[12px] text-cool-grey uppercase tracking-[0.05em]">Service Area</p>
                  <p className="font-body text-[13px] text-deep-navy">{programs.service_area}</p>
                </div>
              </div>
            )}
            {programs.accreditations && programs.accreditations.length > 0 && (
              <div className="flex items-start gap-3">
                <span className="text-[16px]">✓</span>
                <div>
                  <p className="font-body text-[12px] text-cool-grey uppercase tracking-[0.05em]">Accreditations</p>
                  <div className="space-y-1">
                    {programs.accreditations.map((acc, idx) => (
                      <p key={idx} className="font-body text-[13px] text-deep-navy">{acc}</p>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>
          {programs.programs_verified_date && (
            <p className="font-body text-[11px] text-cool-grey/60 mt-2">
              Last updated: {new Date(programs.programs_verified_date).toLocaleDateString()}
            </p>
          )}
        </div>
      )}

      {loading && (
        <div className="flex items-center gap-2">
          <div className="h-2 w-2 bg-soft-gold rounded-full animate-pulse" />
          <p className="font-body text-[12px] text-cool-grey">Loading additional information...</p>
        </div>
      )}
    </div>
  )
}
