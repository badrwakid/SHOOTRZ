import React from 'react'
import { Text, type StyleProp, type TextStyle } from 'react-native'
import { useTokens } from '../theme/useTokens'
import type { TypographyRole } from '../constants/theme'

type Props = {
	role: TypographyRole
	children: React.ReactNode
	style?: StyleProp<TextStyle>
}

export function TextRole({ role, children, style }: Props) {
	const t = useTokens()

	return <Text style={[t.typography[role], style]}>{children}</Text>
}
