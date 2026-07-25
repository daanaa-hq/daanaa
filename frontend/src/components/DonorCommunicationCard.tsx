import React, { useState, useEffect } from 'react'
import TemplateEditorModal from './TemplateEditorModal'
import { type DonorTemplate } from '../lib/schemas'
import { CardPattern } from './ui/CardPattern'

interface DonorCommunicationCardProps {
  nonprofitEin: string
  nonprofitName: string
  authToken: string
}

/**
 * DonorCommunicationCard
 *
 * Dashboard card for donor thank-you templates:
 * - Template selector dropdown (defaults + custom)
 * - Live preview area with variable substitution
 * - Copy to clipboard button
 * - Save custom template button (opens TemplateEditorModal)
 *
 * Fetches from GET /api/nonprofit/donor-templates
 */
export default function DonorCommunicationCard({
  nonprofitEin,
  nonprofitName,
  authToken,
}: DonorCommunicationCardProps) {
  const [templates, setTemplates] = useState<DonorTemplate[]>([])
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>('')
  const [modalOpen, setModalOpen] = useState(false)
  const [loading, setLoading] = useState(true)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    fetchTemplates()
  }, [])

  const fetchTemplates = async () => {
    try {
      setLoading(true)
      const response = await fetch('/api/nonprofit/donor-templates', {
        headers: {
          Authorization: `Bearer ${authToken}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) throw new Error('Failed to load templates')

      const data = await response.json()
      setTemplates(data.templates || [])

      // Auto-select first template
      if (data.templates && data.templates.length > 0) {
        setSelectedTemplateId(data.templates[0].id)
      }
    } catch (err) {
      console.error('Failed to load templates:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleSaveNewTemplate = () => {
    // Refresh templates after saving
    fetchTemplates()
    setModalOpen(false)
  }

  const selectedTemplate = templates.find(t => t.id === selectedTemplateId)
  const preview = selectedTemplate?.sample_preview || ''

  const handleCopyPreview = async () => {
    try {
      await navigator.clipboard.writeText(preview)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch (err) {
      console.error('Failed to copy:', err)
    }
  }

  if (loading) {
    return (
      <CardPattern variant="gradient" className="flex items-center justify-center min-h-40">
        <div className="w-8 h-8 border-4 border-soft-gold border-t-transparent rounded-full animate-spin" />
      </CardPattern>
    )
  }

  return (
    <>
      <CardPattern variant="gradient">
        <div className="flex items-start justify-between mb-4">
          <h3 className="font-display text-xl text-deep-navy">Donor Communication</h3>
          <span className="text-2xl">💬</span>
        </div>

        <p className="text-sm text-cool-grey mb-4">
          Customize thank-you messages for your donors with template variables.
        </p>

        {/* Template Selector */}
        <div className="mb-4">
          <label className="block text-xs font-semibold text-cool-grey mb-2">Select Template</label>
          <select
            value={selectedTemplateId}
            onChange={e => setSelectedTemplateId(e.target.value)}
            className="w-full px-3 py-2 border border-light-grey rounded-lg font-body text-sm focus:outline-none focus:ring-2 focus:ring-soft-gold/50"
          >
            {templates.map(t => (
              <option key={t.id} value={t.id}>
                {t.template_name}
              </option>
            ))}
          </select>
        </div>

        {/* Preview */}
        <div className="mb-4">
          <label className="block text-xs font-semibold text-cool-grey mb-2">Preview</label>
          <CardPattern variant="subtle" className="text-sm leading-relaxed max-h-32 overflow-y-auto">
            <p className="text-deep-navy whitespace-pre-wrap">{preview}</p>
          </CardPattern>
        </div>

        {/* Variables Hint */}
        <p className="text-xs text-cool-grey bg-white px-3 py-2 rounded border border-light-grey mb-4">
          Available variables: {'{donor_name}'}, {'{amount}'}, {'{date}'}, {'{org_name}'}
        </p>

        {/* Action Buttons */}
        <div className="flex gap-2">
          <button
            onClick={handleCopyPreview}
            className="flex-1 px-3 py-2 bg-purple-500 text-white rounded-lg font-semibold text-sm hover:bg-purple-600 transition-colors"
          >
            {copied ? '✓ Copied!' : 'Copy to Clipboard'}
          </button>
          <button
            onClick={() => setModalOpen(true)}
            className="flex-1 px-3 py-2 bg-light-grey text-deep-navy rounded-lg font-semibold text-sm hover:bg-light-grey/70 transition-colors"
          >
            Create Custom
          </button>
        </div>
      </CardPattern>

      {/* Template Editor Modal */}
      <TemplateEditorModal
        isOpen={modalOpen}
        onClose={() => setModalOpen(false)}
        nonprofitEin={nonprofitEin}
        nonprofitName={nonprofitName}
        authToken={authToken}
        onSave={handleSaveNewTemplate}
      />
    </>
  )
}
