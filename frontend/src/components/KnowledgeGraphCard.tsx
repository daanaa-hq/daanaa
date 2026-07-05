import { KGEntity, KGRelationship } from '../data/api';

interface KnowledgeGraphCardProps {
  entities: KGEntity[];
  relationships: KGRelationship[];
}

export default function KnowledgeGraphCard({ entities, relationships }: KnowledgeGraphCardProps) {
  if (entities.length === 0 && relationships.length === 0) {
    return null;
  }

  // Group entities by type
  const entityGroups = entities.reduce(
    (acc, ent) => {
      const type = ent.entity_type || 'Other';
      if (!acc[type]) acc[type] = [];
      acc[type].push(ent);
      return acc;
    },
    {} as Record<string, KGEntity[]>,
  );

  const typeLabels: Record<string, string> = {
    cause: '🎯 Cause Areas',
    location: '📍 Geographic Focus',
    funding_model: '💰 Funding Model',
    population_served: '👥 Populations Served',
    peer_network: '🤝 Peer Network',
    other: 'Other',
  };

  return (
    <div className="mt-6 pt-6 border-t border-navy-light/20">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-lg">🔗</span>
        <h3 className="font-semibold text-cool-grey">Related Organizations & Insights</h3>
      </div>

      {/* Entities grouped by type */}
      {Object.entries(entityGroups).length > 0 && (
        <div className="space-y-4">
          {Object.entries(entityGroups)
            .sort(([aType]) => (aType === 'cause' ? -1 : aType === 'location' ? -2 : 0))
            .map(([type, items]) => (
              <div key={type}>
                <h4 className="text-sm font-medium text-cool-grey/80 mb-2">
                  {typeLabels[type] || type}
                </h4>
                <div className="flex flex-wrap gap-2">
                  {items.map((entity, idx) => (
                    <span
                      key={idx}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-soft-gold/5 border border-soft-gold/20 rounded-full text-cool-grey text-sm font-medium hover:bg-soft-gold/10 transition-colors"
                      title={entity.confidence ? `Confidence: ${(entity.confidence * 100).toFixed(0)}%` : undefined}
                    >
                      {entity.entity_value}
                      {entity.confidence && entity.confidence < 0.9 && (
                        <span className="text-xs text-cool-grey/60">
                          ({(entity.confidence * 100).toFixed(0)}%)
                        </span>
                      )}
                    </span>
                  ))}
                </div>
              </div>
            ))}
        </div>
      )}

      {/* Relationships */}
      {relationships.length > 0 && (
        <div className="mt-4">
          <h4 className="text-sm font-medium text-cool-grey/80 mb-2">
            🔗 Connections ({relationships.length})
          </h4>
          <p className="text-xs text-cool-grey/60">
            This organization has {relationships.length} identified connection{relationships.length !== 1 ? 's' : ''} to similar organizations in the network.
          </p>
        </div>
      )}

      <div className="mt-3 text-xs text-cool-grey/60 flex items-center gap-1">
        <span>✨</span>
        <span>Extracted via GPU-accelerated entity recognition</span>
      </div>
    </div>
  );
}
