import { tokens } from '../tokens'
import { typographyRoleMap } from '../typography'

describe('design token contract (v3)', () => {
	test('focus token is structured (RN-safe)', () => {
		expect(tokens.focus.ringWidth).toBe(2)
		expect(typeof tokens.focus.ringColor).toBe('string')
		expect(tokens.focus.ringColor).toBe(tokens.focus.ring)
	})

	test('core semantic surfaces and brand are stable', () => {
		expect(tokens.bg.primary).toBe('#0F141B')
		expect(tokens.brand.primary).toBe('#E8521A')
		expect(tokens.brand.accent).toBe('#00D4FF')
	})

	test('motion duration scale is numeric (ms)', () => {
		expect(tokens.motion.duration.instant).toBe(100)
		expect(tokens.motion.duration.fast).toBe(200)
		expect(tokens.motion.duration.normal).toBe(300)
		expect(tokens.motion.duration.reveal).toBe(1400)
		expect(tokens.motion.duration.typingStagger).toBe(150)
		expect(tokens.motion.duration.typingPulse).toBe(350)
	})

	test('chat surfaces use 8-digit brand hex (not raw rgba in components)', () => {
		expect(tokens.chat.userBubble).toMatch(/^#E8521A[0-9A-Fa-f]{2}$/)
		expect(tokens.chat.userBorder).toMatch(/^#E8521A[0-9A-Fa-f]{2}$/)
	})

	test('typography role map has expected v3 display + button roles', () => {
		expect(typographyRoleMap.display).toBeDefined()
		expect(typographyRoleMap.headingLg).toBeDefined()
		expect(typographyRoleMap.button).toBeDefined()
	})
})
