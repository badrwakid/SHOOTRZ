import { semanticTokens } from './tokens'
import { typographyRoleMap } from './typography'

const tokenBundle = {
	tokens: semanticTokens,
	typography: typographyRoleMap,
} as const

export function useTokens() {
	return tokenBundle
}
