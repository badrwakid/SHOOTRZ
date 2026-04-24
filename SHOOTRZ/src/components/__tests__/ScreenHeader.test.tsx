import React from 'react'
import { render } from '@testing-library/react-native'
import { ScreenHeader } from '../ScreenHeader'

describe('ScreenHeader', () => {
	it('renders title and subtitle text', () => {
		const { getByText } = render(
			<ScreenHeader title="Progress" subtitle="Weekly trend" />,
		)

		expect(getByText('Progress')).toBeTruthy()
		expect(getByText('Weekly trend')).toBeTruthy()
	})
})
