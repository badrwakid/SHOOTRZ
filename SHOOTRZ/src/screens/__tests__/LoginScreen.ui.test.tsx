import React from 'react'
import { fireEvent, render } from '@testing-library/react-native'
import { ScreenHeader } from '../../components/ScreenHeader'
import { SectionHeader } from '../../components/SectionHeader'
import { LoginScreen } from '../LoginScreen'

jest.mock('../../context/AuthContext', () => ({
	useAuth: () => ({
		login: jest.fn(),
		signup: jest.fn(),
		resetPassword: jest.fn(),
		signInWithApple: jest.fn(),
		signInWithGoogle: jest.fn(),
		setUser: jest.fn(),
		setIsNewUser: jest.fn(),
		isAuthenticated: false,
		setNavigationCallback: jest.fn(),
	}),
}))

jest.mock('../../utils/hapticFeedback', () => ({
	hapticFeedback: {
		warning: jest.fn(),
		medium: jest.fn(),
		success: jest.fn(),
		selection: jest.fn(),
	},
}))

test('login heading renders', () => {
	const { getByText } = render(<LoginScreen onLogin={() => {}} />)
	expect(getByText(/Welcome Back/i)).toBeTruthy()
})

test('login CTA still exists after global style migration', () => {
	const { getByText } = render(<LoginScreen onLogin={() => {}} />)
	// Exact match: subtitle contains "Sign in" which also matches /SIGN IN/i
	expect(getByText('SIGN IN', { exact: true })).toBeTruthy()
})

test('screen header renders title and subtitle text', () => {
	const { getByText } = render(
		<ScreenHeader title="Progress" subtitle="Weekly trend" />,
	)

	expect(getByText('Progress')).toBeTruthy()
	expect(getByText('Weekly trend')).toBeTruthy()
})

test('section header action callback fires on press', () => {
	const onPress = jest.fn()
	const { getByRole } = render(
		<SectionHeader title="Workouts" action={{ label: 'See all', onPress }} />,
	)

	fireEvent.press(getByRole('button'))
	expect(onPress).toHaveBeenCalledTimes(1)
})
