import { colors, getScoreTier } from '../../constants/theme'
import { semanticTokens } from '../../theme/tokens'

describe('InputField theme tokens', () => {
	it('uses v3 primary background token value', () => {
		expect(colors.bg.primary).toBe('#0F141B')
	})

	it('forwards semantic color groups for migration safety', () => {
		expect(colors.text.primary).toBe(semanticTokens.text.primary)
		expect(colors.border.default).toBe(semanticTokens.border.default)
		expect(colors.brand.chrome).toBe(semanticTokens.brand.chrome)
		expect(colors.success).toBe(semanticTokens.state.success)
	})

	it('keeps legacy aliases mapped to semantic tokens', () => {
		expect(colors.bg.void).toBe(semanticTokens.bg.canvas)
		expect(colors.brand.orange).toBe(semanticTokens.brand.primary)
		expect(colors.brand.cyan).toBe(semanticTokens.brand.accent)
		expect(colors.border.cyan).toBe(semanticTokens.border.accent)
	})

	it('keeps score tier mapping stable for score 82', () => {
		expect(getScoreTier(82)).toBe('great')
	})
})
