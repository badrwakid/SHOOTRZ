import React from 'react'
import { fireEvent, render } from '@testing-library/react-native'
import { StyleSheet } from 'react-native'
import { PrimaryButton } from '../PrimaryButton'

describe('PrimaryButton', () => {
	it('renders uppercase label ANALYZE SHOT', () => {
		const handlePress = jest.fn()

		const { getByText } = render(
			<PrimaryButton label="Analyze Shot" onPress={handlePress} />,
		)

		expect(getByText('ANALYZE SHOT')).toBeTruthy()
	})

	it('fires onPress when enabled', () => {
		const handlePress = jest.fn()
		const { getByRole } = render(
			<PrimaryButton label="Analyze Shot" onPress={handlePress} />,
		)

		fireEvent.press(getByRole('button'))

		expect(handlePress).toHaveBeenCalledTimes(1)
	})

	it('does not fire onPress when disabled', () => {
		const handlePress = jest.fn()
		const { getByRole } = render(
			<PrimaryButton label="Analyze Shot" onPress={handlePress} disabled />,
		)

		const button = getByRole('button')
		fireEvent.press(button)

		expect(button.props.accessibilityState?.disabled).toBe(true)
		expect(handlePress).not.toHaveBeenCalled()
	})

	it('does not fire onPress when loading and keeps predictable render output', () => {
		const handlePress = jest.fn()
		const { getByRole, queryByText } = render(
			<PrimaryButton label="Analyze Shot" onPress={handlePress} loading />,
		)

		const button = getByRole('button')
		fireEvent.press(button)

		expect(button.props.accessibilityState?.disabled).toBe(true)
		expect(handlePress).not.toHaveBeenCalled()
		expect(queryByText('ANALYZE SHOT')).toBeNull()
	})

	it('disabled button is not interactive and reports disabled to assistive services', () => {
		const handlePress = jest.fn()
		const { getByRole, getByText } = render(
			<PrimaryButton label="Analyze" onPress={handlePress} disabled />,
		)

		const btn = getByRole('button')
		expect(btn.props.accessibilityState?.disabled).toBe(true)
		const label = getByText('ANALYZE')
		const labelStyle = StyleSheet.flatten(label.props.style)
		expect(labelStyle.color).toBe('#475569')
		fireEvent.press(btn)
		expect(handlePress).not.toHaveBeenCalled()
	})
})
