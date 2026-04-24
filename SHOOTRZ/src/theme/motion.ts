import { semanticTokens } from './tokens'

const d = semanticTokens.motion.duration

/**
 * Shared motion tokens for RN Animated / interaction timing.
 * Durations are derived from `semanticTokens.motion.duration` to avoid drift.
 */
export const motion = {
	timing: {
		fast: d.fast,
		/** Alias of `normal` for legacy call sites. */
		medium: d.normal,
		reveal: d.reveal,
		stagger: d.typingStagger,
		typingPulse: d.typingPulse,
	},
	scale: { press: 0.97 },
} as const

export type MotionTokens = typeof motion
