// ═══════════════════════════════════════════════
// SHOOTRZ Design System v2 — Premium Sports-Tech
// ═══════════════════════════════════════════════

export const colors = {
	bg: {
		void: '#080A0E',
		primary: '#0D1117',
		secondary: '#13181F',
		elevated: '#1A2030',
		overlay: '#1F2737',
	},
	brand: {
		orange: '#E8521A',
		orangeLight: '#FF6B2B',
		orangeDim: '#E8521A22',
		orangeGlow: '#E8521A40',
		cyan: '#00D4FF',
		cyanLight: '#33DFFF',
		cyanDim: '#00D4FF18',
		chrome: '#C8D0DC',
		chromeMid: '#8B95A3',
		chromeDim: '#FFFFFF0A',
	},
	score: {
		elite: { bg: '#FFD700', text: '#1A1400', glow: '#FFD70040' },
		great: { bg: '#22C55E', text: '#0A1F14', glow: '#22C55E40' },
		good: { bg: '#3B82F6', text: '#0A1529', glow: '#3B82F640' },
		fair: { bg: '#F59E0B', text: '#1F1500', glow: '#F59E0B40' },
		poor: { bg: '#EF4444', text: '#1F0A0A', glow: '#EF444440' },
	},
	text: {
		primary: '#F0F4F8',
		secondary: '#8B95A3',
		tertiary: '#4A5568',
		inverse: '#0D1117',
	},
	border: {
		subtle: '#FFFFFF08',
		default: '#FFFFFF12',
		strong: '#FFFFFF20',
		brand: '#E8521A40',
		cyan: '#00D4FF30',
	},
	success: '#22C55E',
	warning: '#F59E0B',
	error: '#EF4444',
	info: '#3B82F6',
} as const

export type ScoreTier = 'elite' | 'great' | 'good' | 'fair' | 'poor'

export function getScoreTier(score: number): ScoreTier {
	if (score >= 90) return 'elite'
	if (score >= 75) return 'great'
	if (score >= 60) return 'good'
	if (score >= 40) return 'fair'
	return 'poor'
}

export function getScoreColor(score: number) {
	return colors.score[getScoreTier(score)]
}

export const typography = {
	size: {
		xs: 11,
		sm: 13,
		base: 15,
		md: 17,
		lg: 20,
		xl: 24,
		'2xl': 30,
		'3xl': 38,
		'4xl': 48,
	},
	weight: {
		regular: '400' as const,
		medium: '500' as const,
		semibold: '600' as const,
		bold: '700' as const,
		heavy: '800' as const,
		black: '900' as const,
	},
	lineHeight: {
		tight: 1.15,
		snug: 1.3,
		normal: 1.5,
		relaxed: 1.75,
	},
	tracking: {
		tight: -0.5,
		normal: 0,
		wide: 0.5,
		wider: 1.0,
		widest: 2.0,
	},
} as const

export const spacing = {
	0: 0,
	1: 4,
	2: 8,
	3: 12,
	4: 16,
	5: 20,
	6: 24,
	7: 28,
	8: 32,
	10: 40,
	12: 48,
	16: 64,
	20: 80,
	screenPadding: 16,
	cardPadding: 16,
	sectionGap: 24,
	itemGap: 12,
	tabBarHeight: 84,
	headerHeight: 56,
} as const

export const radius = {
	xs: 4,
	sm: 8,
	md: 12,
	lg: 16,
	xl: 20,
	'2xl': 24,
	'3xl': 32,
	full: 9999,
	card: 16,
	button: 12,
	pill: 9999,
	badge: 8,
	avatar: 9999,
} as const

export const glass = {
	card: {
		bg: 'rgba(13, 17, 23, 0.75)',
		border: 'rgba(255, 255, 255, 0.08)',
		radius: 16,
	},
	sheet: {
		bg: 'rgba(8, 10, 14, 0.85)',
		border: 'rgba(255, 255, 255, 0.06)',
		radius: 24,
	},
	orange: {
		bg: 'rgba(232, 82, 26, 0.12)',
		border: 'rgba(232, 82, 26, 0.25)',
		radius: 16,
	},
	cyan: {
		bg: 'rgba(0, 212, 255, 0.08)',
		border: 'rgba(0, 212, 255, 0.20)',
		radius: 16,
	},
} as const

export const animation = {
	duration: {
		instant: 100,
		fast: 200,
		normal: 300,
		slow: 500,
		deliberate: 800,
	},
	easing: {
		spring: { damping: 15, stiffness: 150, mass: 1 },
		springSnappy: { damping: 20, stiffness: 300 },
		springBouncy: { damping: 10, stiffness: 100 },
	},
} as const

export const shadows = {
	sm: {
		shadowColor: '#000',
		shadowOffset: { width: 0, height: 2 },
		shadowOpacity: 0.3,
		shadowRadius: 4,
		elevation: 3,
	},
	md: {
		shadowColor: '#000',
		shadowOffset: { width: 0, height: 4 },
		shadowOpacity: 0.4,
		shadowRadius: 8,
		elevation: 6,
	},
	orange: {
		shadowColor: '#E8521A',
		shadowOffset: { width: 0, height: 4 },
		shadowOpacity: 0.35,
		shadowRadius: 12,
		elevation: 8,
	},
	cyan: {
		shadowColor: '#00D4FF',
		shadowOffset: { width: 0, height: 4 },
		shadowOpacity: 0.25,
		shadowRadius: 12,
		elevation: 8,
	},
} as const

// ═══════════════════════════════════════════════
// Legacy theme — preserved for backward compatibility.
// New code should import { colors, typography, spacing, ... } directly.
// ═══════════════════════════════════════════════

export const SHOOTRZ_THEME = {
	colors: {
		background: colors.bg.primary,
		surface: colors.bg.secondary,
		surfaceElevated: colors.bg.elevated,
		primary: colors.brand.orange,
		primaryLight: colors.brand.orangeLight,
		primaryDark: '#E65100',
		secondary: colors.brand.cyan,
		secondaryLight: colors.brand.cyanLight,
		secondaryDark: '#1976D2',
		textPrimary: colors.text.primary,
		textSecondary: colors.text.secondary,
		textMuted: colors.text.tertiary,
		accent: colors.brand.cyan,
		success: colors.success,
		warning: colors.warning,
		error: colors.error,
		circuitGlow: '#00E5FF',
		circuitLine: '#42A5F5',
	},
	typography: {
		heading1: {
			fontSize: 32,
			fontWeight: 'bold' as const,
			color: colors.text.primary,
			letterSpacing: 1,
		},
		heading2: {
			fontSize: 24,
			fontWeight: 'bold' as const,
			color: colors.text.primary,
			letterSpacing: 0.5,
		},
		heading3: {
			fontSize: 20,
			fontWeight: '600' as const,
			color: colors.text.primary,
		},
		body: {
			fontSize: 16,
			fontWeight: 'normal' as const,
			color: colors.text.secondary,
			lineHeight: 24,
		},
		bodySmall: {
			fontSize: 14,
			fontWeight: 'normal' as const,
			color: colors.text.secondary,
			lineHeight: 20,
		},
		button: {
			fontSize: 16,
			fontWeight: 'bold' as const,
			color: colors.text.primary,
		},
		caption: {
			fontSize: 12,
			fontWeight: 'normal' as const,
			color: colors.text.tertiary,
		},
	},
	spacing: {
		xs: 4,
		sm: 8,
		md: 16,
		lg: 24,
		xl: 32,
		xxl: 48,
	},
	borderRadius: {
		sm: 8,
		md: 12,
		lg: 16,
		xl: 24,
		round: 50,
	},
	shadows: {
		small: shadows.sm,
		medium: shadows.md,
		large: shadows.orange,
	},
	gradients: {
		primary: [colors.brand.orange, colors.brand.orangeLight],
		primaryDark: ['#E65100', colors.brand.orange],
		secondary: [colors.brand.cyan, colors.brand.cyanLight],
		secondaryDark: ['#1976D2', colors.brand.cyan],
		circuit: ['#00E5FF', '#42A5F5'],
		accent: [colors.brand.cyan, '#00E5FF'],
		success: [colors.success, '#66BB6A'],
		card: ['rgba(19, 24, 31, 0.8)', 'rgba(26, 32, 48, 0.95)'],
		orange_glow: ['rgba(232, 82, 26, 0.2)', 'rgba(232, 82, 26, 0)'],
		blue_glow: ['rgba(0, 212, 255, 0.2)', 'rgba(0, 212, 255, 0)'],
	},
	animations: {
		fast: animation.duration.fast,
		normal: animation.duration.normal,
		slow: animation.duration.slow,
		verySlow: animation.duration.deliberate,
	},
	easing: {
		easeInOut: 'ease-in-out',
		easeOut: 'ease-out',
		spring: 'spring',
	},
}

export const COMPONENT_STYLES = {
	button: {
		primary: {
			backgroundColor: colors.brand.orange,
			borderRadius: radius.button,
			paddingVertical: spacing[4],
			paddingHorizontal: spacing[6],
			...shadows.orange,
		},
		secondary: {
			backgroundColor: 'transparent',
			borderWidth: 2,
			borderColor: colors.brand.cyan,
			borderRadius: radius.button,
			paddingVertical: spacing[4],
			paddingHorizontal: spacing[6],
		},
	},
	card: {
		backgroundColor: colors.bg.secondary,
		borderRadius: radius.card,
		padding: spacing.cardPadding,
		...shadows.md,
		borderWidth: 1,
		borderColor: colors.border.default,
	},
	input: {
		backgroundColor: colors.bg.elevated,
		borderColor: colors.border.default,
		borderWidth: 1,
		borderRadius: radius.md,
		padding: spacing[4],
		color: colors.text.primary,
	},
}
