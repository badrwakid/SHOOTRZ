/**
 * v3 button scales and AA-oriented palette (see design-system rollout).
 */
export const V3_ORANGE = { default: '#BB3F15', pressed: '#9E3512' } as const
export const V3_CYAN = { default: '#0D9488', pressed: '#0F766E' } as const
export const V3_DANGER = { default: '#B91C1C', pressed: '#991B1B' } as const

export const ORANGE_STROKE = V3_ORANGE.default

export const DISABLED_SLATE = { bg: '#1C2432', label: '#475569' } as const

export const SIZE = {
	sm: { height: 36, px: 14, radius: 8, font: 11, icon: 14, gap: 6 },
	md: { height: 44, px: 20, radius: 10, font: 13, icon: 16, gap: 8 },
	lg: { height: 52, px: 28, radius: 12, font: 14, icon: 18, gap: 10 },
} as const

export type ButtonSizeKey = keyof typeof SIZE
