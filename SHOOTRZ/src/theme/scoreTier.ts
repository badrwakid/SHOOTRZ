import { colors } from '../constants/theme'
import type { ScoreTier } from '../constants/theme'

export const SCORE_TIER_LABELS: Record<ScoreTier, string> = {
	elite: 'ELITE',
	great: 'GREAT',
	good: 'GOOD',
	fair: 'FAIR',
	poor: 'POOR',
}

/** Ring stroke = solid tier color; single source: `colors.score` in `constants/theme` */
export const SCORE_TIER_RING_STROKE: Record<ScoreTier, string> = {
	poor: colors.score.poor.bg,
	fair: colors.score.fair.bg,
	good: colors.score.good.bg,
	great: colors.score.great.bg,
	elite: colors.score.elite.bg,
}

export const SCORE_TIER_CARD_SURFACE: Record<ScoreTier, { bg: string; border: string }> = {
	poor: { bg: 'rgba(239, 68, 68, 0.12)', border: 'rgba(239, 68, 68, 0.3)' },
	fair: { bg: 'rgba(245, 158, 11, 0.12)', border: 'rgba(245, 158, 11, 0.3)' },
	good: { bg: 'rgba(251, 191, 36, 0.12)', border: 'rgba(251, 191, 36, 0.3)' },
	great: { bg: 'rgba(34, 197, 94, 0.12)', border: 'rgba(34, 197, 94, 0.3)' },
	elite: { bg: 'rgba(20, 199, 224, 0.12)', border: 'rgba(20, 199, 224, 0.3)' },
}

export const SCORE_TIER_BADGE: Record<ScoreTier, { bg: string; text: string }> = {
	poor: { bg: 'rgba(239, 68, 68, 0.18)', text: colors.score.poor.text },
	fair: { bg: 'rgba(245, 158, 11, 0.2)', text: colors.score.fair.text },
	good: { bg: 'rgba(251, 191, 36, 0.2)', text: colors.score.good.text },
	great: { bg: 'rgba(34, 197, 94, 0.2)', text: colors.score.great.text },
	elite: { bg: 'rgba(20, 199, 224, 0.2)', text: colors.score.elite.text },
}
