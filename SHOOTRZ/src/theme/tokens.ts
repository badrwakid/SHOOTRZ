export const semanticTokens = {
	bg: {
		canvas: '#080A0E',
		primary: '#0F141B',
		secondary: '#13181F',
		elevated: '#1A2030',
		overlay: '#1F2737',
	},
	text: {
		primary: '#F0F4F8',
		secondary: '#8B95A3',
		tertiary: '#4A5568',
		inverse: '#0F141B',
	},
	border: {
		subtle: '#FFFFFF08',
		default: '#FFFFFF12',
		strong: '#FFFFFF20',
		brand: '#E8521A40',
		accent: '#00D4FF30',
	},
	brand: {
		primary: '#E8521A',
		primaryLight: '#FF6B2B',
		primaryDim: '#E8521A22',
		primaryGlow: '#E8521A40',
		accent: '#00D4FF',
		accentLight: '#33DFFF',
		accentDim: '#00D4FF18',
		chrome: '#C8D0DC',
		chromeMid: '#8B95A3',
		chromeDim: '#FFFFFF0A',
	},
	state: {
		success: '#22C55E',
		warning: '#F59E0B',
		error: '#EF4444',
		info: '#3B82F6',
	},
	focus: {
		/** Logical px — matches `FocusRing` default; keep in sync with `FocusRingToken.width`. */
		ringWidth: 2,
		/** Focus ring stroke; alias of `ring` for contract consumers. */
		ringColor: '#00D4FF',
		ring: '#00D4FF',
		ringSoft: '#00D4FF30',
	},
	/** OAuth / social sign-in (brand-fixed surfaces; values live in tokens for lint in screens). */
	oauth: {
		google: { surface: '#FFFFFF', label: '#1F1F1F' },
		apple: { surface: '#000000', label: '#FFFFFF' },
	},
	shadow: {
		base: '#000000',
		brand: '#E8521A',
		accent: '#00D4FF',
	},
	/** Chat surfaces (8-digit hex = RGBA on RN). */
	chat: {
		userBubble: '#E8521A26',
		userBorder: '#E8521A4D',
	},
	motion: {
		duration: {
			instant: 100,
			fast: 200,
			normal: 300,
			slow: 500,
			deliberate: 800,
			/** Long reveal / hero timing (ms). */
			reveal: 1400,
			/** Stagger between typing-indicator dots (ms). */
			typingStagger: 150,
			/** Half-pulse duration for each typing dot (ms). */
			typingPulse: 350,
		},
	},
} as const

/** Alias for design-system contract tests and imports that expect `tokens`. */
export const tokens = semanticTokens

export type SemanticTokens = typeof semanticTokens
