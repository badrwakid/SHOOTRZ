// ═══════════════════════════════════════════════
// SHOOTRZ Design System v2 — Premium Sports-Tech
// ═══════════════════════════════════════════════

import { semanticTokens } from '../theme/tokens'
import { typographyRoleMap } from '../theme/typography'

const legacyColorAliases = {
	bg: {
		// Legacy alias kept for backward compatibility with v2 callers.
		void: semanticTokens.bg.canvas,
	},
	brand: {
		// Legacy aliases mapped to semantic brand tokens.
		orange: semanticTokens.brand.primary,
		orangeLight: semanticTokens.brand.primaryLight,
		orangeDim: semanticTokens.brand.primaryDim,
		orangeGlow: semanticTokens.brand.primaryGlow,
		cyan: semanticTokens.brand.accent,
		cyanLight: semanticTokens.brand.accentLight,
		cyanDim: semanticTokens.brand.accentDim,
	},
	border: {
		// Legacy alias mapped to semantic accent border.
		cyan: semanticTokens.border.accent,
	},
} as const

export const colors = {
	bg: {
		...semanticTokens.bg,
		...legacyColorAliases.bg,
	},
	brand: {
		...semanticTokens.brand,
		...legacyColorAliases.brand,
	},
	// v3 score tiers (align with `src/theme/scoreTier.ts` ring/badge semantics):
	// poor red, fair amber, good yellow, great green, elite cyan.
	score: {
		poor: {
			bg: semanticTokens.state.error,
			text: semanticTokens.state.error,
			glow: '#EF444440',
		},
		fair: {
			bg: semanticTokens.state.warning,
			text: semanticTokens.state.warning,
			glow: '#F59E0B40',
		},
		good: {
			bg: '#FBBF24',
			text: '#FBBF24',
			glow: '#FBBF2440',
		},
		great: {
			bg: semanticTokens.state.success,
			text: semanticTokens.state.success,
			glow: '#22C55E40',
		},
		elite: {
			bg: '#14C7E0',
			text: '#14C7E0',
			glow: '#14C7E040',
		},
	},
	text: {
		...semanticTokens.text,
	},
	chat: {
		userBubble: semanticTokens.chat.userBubble,
		userBorder: semanticTokens.chat.userBorder,
	},
	border: {
		...semanticTokens.border,
		...legacyColorAliases.border,
	},
	success: semanticTokens.state.success,
	warning: semanticTokens.state.warning,
	error: semanticTokens.state.error,
	info: semanticTokens.state.info,
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
	roles: typographyRoleMap,
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

export const typographyRoles = typography.roles
export type TypographyRole = keyof typeof typographyRoles

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
	duration: semanticTokens.motion.duration,
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
			fontSize: typographyRoleMap.display.fontSize,
			fontWeight: typographyRoleMap.display.fontWeight,
			color: colors.text.primary,
			letterSpacing: typographyRoleMap.display.letterSpacing,
		},
		heading2: {
			fontSize: typographyRoleMap.headingMd.fontSize,
			fontWeight: typographyRoleMap.headingMd.fontWeight,
			color: colors.text.primary,
			letterSpacing: typographyRoleMap.headingMd.letterSpacing,
		},
		heading3: {
			fontSize: typographyRoleMap.headingSm.fontSize,
			fontWeight: typographyRoleMap.headingSm.fontWeight,
			color: colors.text.primary,
		},
		body: {
			fontSize: typographyRoleMap.body.fontSize,
			fontWeight: typographyRoleMap.body.fontWeight,
			color: colors.text.secondary,
			lineHeight: typographyRoleMap.body.lineHeight,
		},
		bodySmall: {
			fontSize: 14,
			fontWeight: 'normal' as const,
			color: colors.text.secondary,
			lineHeight: 20,
		},
		button: {
			fontSize: typographyRoleMap.button.fontSize,
			fontWeight: typographyRoleMap.button.fontWeight,
			color: colors.text.primary,
		},
		caption: {
			fontSize: typographyRoleMap.caption.fontSize,
			fontWeight: typographyRoleMap.caption.fontWeight,
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
