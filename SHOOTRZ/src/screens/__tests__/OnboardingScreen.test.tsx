import React from 'react'
import { Text } from 'react-native'
import { fireEvent, render, waitFor } from '@testing-library/react-native'

import { OnboardingScreen } from '../OnboardingScreen'

const mockUpdateProfile = jest.fn().mockResolvedValue(undefined)
const mockOnComplete = jest.fn()

jest.mock('react-native-safe-area-context', () => {
	const React = require('react')
	const { View } = require('react-native')
	return {
		SafeAreaView: ({ children }: { children: React.ReactNode }) => <View>{children}</View>,
	}
})

jest.mock('@expo/vector-icons', () => {
	const React = require('react')
	const { Text } = require('react-native')
	return {
		Ionicons: ({ name }: { name: string }) => <Text>{name}</Text>,
	}
})

jest.mock('../../components/PrimaryButton', () => {
	const React = require('react')
	const { Text, TouchableOpacity } = require('react-native')
	return {
		PrimaryButton: ({
			label,
			onPress,
			loading,
		}: {
			label: string
			onPress: () => void
			loading?: boolean
		}) => (
			<TouchableOpacity onPress={onPress} disabled={loading}>
				<Text>{label}</Text>
			</TouchableOpacity>
		),
	}
})

jest.mock('../../context/AuthContext', () => ({
	useAuth: () => ({
		updateProfile: mockUpdateProfile,
	}),
}))

jest.mock('../../utils/hapticFeedback', () => ({
	hapticFeedback: {
		selection: jest.fn(),
		medium: jest.fn(),
		success: jest.fn(),
		light: jest.fn(),
	},
}))

describe('OnboardingScreen', () => {
	beforeEach(() => {
		jest.clearAllMocks()
	})

	const pressContinueAndWait = async (
		getByText: (text: string) => any,
		expectedTitle?: string,
	) => {
		fireEvent.press(getByText('Continue'))
		if (expectedTitle) {
			await waitFor(() => {
				expect(getByText(expectedTitle)).toBeTruthy()
			})
		}
	}

	test('renders new onboarding cards as user progresses', async () => {
		const { getByText } = render(<OnboardingScreen onComplete={mockOnComplete} />)

		expect(getByText('Welcome to SHOOTRZ')).toBeTruthy()
		await pressContinueAndWait(getByText, 'Your Skill Level')
		await pressContinueAndWait(getByText, 'Your Position')
		await pressContinueAndWait(getByText, 'Primary Goal')
		await pressContinueAndWait(getByText, 'Training Frequency')
		await pressContinueAndWait(getByText, 'Drill Duration')
		await pressContinueAndWait(getByText, 'Dominant Hand')
		await pressContinueAndWait(getByText, 'Experience')
		await pressContinueAndWait(getByText, 'Coaching Style')
		await pressContinueAndWait(getByText, 'Body Metrics')
	})

	test('saves step payloads incrementally', async () => {
		const { getByText } = render(<OnboardingScreen onComplete={mockOnComplete} />)

		// Step 0 -> 1 (no save)
		await pressContinueAndWait(getByText, 'Your Skill Level')

		// Step 1 save
		await pressContinueAndWait(getByText, 'Your Position')
		await waitFor(() => expect(mockUpdateProfile).toHaveBeenCalledWith({ skillLevel: 'beginner' }))

		// Step 2 save
		await pressContinueAndWait(getByText, 'Primary Goal')
		await waitFor(() => expect(mockUpdateProfile).toHaveBeenCalledWith({ position: 'Guard' }))

		// Step 3 save
		await pressContinueAndWait(getByText, 'Training Frequency')
		await waitFor(() =>
			expect(mockUpdateProfile).toHaveBeenCalledWith({ primaryGoal: 'Improve shooting accuracy' }),
		)
	})

	test('validates numeric input before save', async () => {
		const { getByText, getByPlaceholderText } = render(<OnboardingScreen onComplete={mockOnComplete} />)

		// Move to drill duration step (5)
		await pressContinueAndWait(getByText, 'Your Skill Level')
		await pressContinueAndWait(getByText, 'Your Position')
		await pressContinueAndWait(getByText, 'Primary Goal')
		await pressContinueAndWait(getByText, 'Training Frequency')
		await pressContinueAndWait(getByText, 'Drill Duration')

		const durationInput = getByPlaceholderText('e.g. 30')
		fireEvent.changeText(durationInput, 'abc')
		fireEvent.press(getByText('Continue'))

		expect(getByText('Please enter a valid drill duration in minutes.')).toBeTruthy()
		expect(mockUpdateProfile).not.toHaveBeenCalledWith({ preferredDrillDuration: expect.any(Number) })
	})

	test('completes flow and calls onComplete', async () => {
		const { getByText } = render(<OnboardingScreen onComplete={mockOnComplete} />)

		await pressContinueAndWait(getByText, 'Your Skill Level')
		await pressContinueAndWait(getByText, 'Your Position')
		await pressContinueAndWait(getByText, 'Primary Goal')
		await pressContinueAndWait(getByText, 'Training Frequency')
		await pressContinueAndWait(getByText, 'Drill Duration')
		await pressContinueAndWait(getByText, 'Dominant Hand')
		await pressContinueAndWait(getByText, 'Experience')
		await pressContinueAndWait(getByText, 'Coaching Style')
		await pressContinueAndWait(getByText, 'Body Metrics')
		fireEvent.press(getByText('Get Started'))

		await waitFor(() => {
			expect(mockOnComplete).toHaveBeenCalledTimes(1)
		})
	})
})

