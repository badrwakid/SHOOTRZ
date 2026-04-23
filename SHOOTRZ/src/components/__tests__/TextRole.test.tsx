import React from 'react'
import { StyleSheet } from 'react-native'
import { render } from '@testing-library/react-native'
import { TextRole } from '../TextRole'
import type { TypographyRole } from '../../constants/theme'

describe('TextRole', () => {
	const fontExpectations: Array<{
		role: TypographyRole
		expectedFontFamily: string
	}> = [
		{ role: 'display', expectedFontFamily: 'BarlowCondensedBlack' },
		{ role: 'headingLg', expectedFontFamily: 'BarlowCondensedBold' },
		{ role: 'headingMd', expectedFontFamily: 'BarlowCondensedBold' },
		{ role: 'headingSm', expectedFontFamily: 'BarlowCondensedBold' },
		{ role: 'body', expectedFontFamily: 'DMSansRegular' },
		{ role: 'bodyStrong', expectedFontFamily: 'DMSansSemiBold' },
		{ role: 'caption', expectedFontFamily: 'DMSansRegular' },
		{ role: 'button', expectedFontFamily: 'DMSansBold' },
	]

	it.each(fontExpectations)(
		'applies $role typography with expected font family',
		({ role, expectedFontFamily }) => {
			const textValue = `role-${role}`
			const { getByText } = render(<TextRole role={role}>{textValue}</TextRole>)
			const text = getByText(textValue)
			const flattenedStyle = StyleSheet.flatten(text.props.style)

			expect(flattenedStyle.fontFamily).toBe(expectedFontFamily)
		},
	)

	it('merges style overrides while preserving base role font family', () => {
		const { getByText } = render(
			<TextRole role="body" style={{ color: '#FF0000' }}>
				override-check
			</TextRole>,
		)
		const text = getByText('override-check')
		const flattenedStyle = StyleSheet.flatten(text.props.style)

		expect(flattenedStyle.color).toBe('#FF0000')
		expect(flattenedStyle.fontFamily).toBe('DMSansRegular')
	})
})
