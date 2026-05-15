import React from 'react'
import { fireEvent, render } from '@testing-library/react-native'
import { SectionHeader } from '../SectionHeader'

describe('SectionHeader', () => {
	it('calls action callback when action is pressed', () => {
		const onPress = jest.fn()
		const { getByRole, getByText } = render(
			<SectionHeader title="Workouts" action={{ label: 'See all', onPress }} />,
		)

		expect(getByText('Workouts')).toBeTruthy()
		fireEvent.press(getByRole('button'))
		expect(onPress).toHaveBeenCalledTimes(1)
	})
})
