import React from 'react'
import { Text } from 'react-native'
import { fireEvent, render, waitFor } from '@testing-library/react-native'
import { ProfileScreen } from '../ProfileScreen'

const mockLogout = jest.fn()
const mockRefresh = jest.fn().mockResolvedValue(undefined)
const mockRefreshStats = jest.fn().mockResolvedValue(undefined)
const mockUpdateProfile = jest.fn().mockResolvedValue({})
const mockUpdatePreferences = jest.fn().mockResolvedValue({})

const mockProfileState: any = {
	profile: {
		id: 'user-1',
		name: 'Task Six User',
		username: 'task6',
		position: 'Guard',
		skill_level: 'advanced',
		profile: {
			notifications_enabled: true,
			dark_mode_enabled: true,
			analytics_enabled: true,
		},
	},
	stats: {
		totalSessions: 17,
		bestScore: 92,
		currentStreak: 8,
	},
	preferences: {
		notifications_enabled: true,
		dark_mode_enabled: true,
		analytics_enabled: true,
	},
	profileLoading: false,
	statsLoading: false,
	profileError: null,
	statsError: null,
	refresh: mockRefresh,
	refreshStats: mockRefreshStats,
	updateProfile: mockUpdateProfile,
	updatePreferences: mockUpdatePreferences,
}

jest.mock('@react-navigation/native', () => ({
	useFocusEffect: (effect: () => void) => {
		effect()
	},
}))

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

jest.mock('../../components/StatCard', () => {
	const React = require('react')
	const { Text } = require('react-native')
	return {
		StatCard: ({ label, value }: { label: string; value: number }) => (
			<Text>{`${label}:${String(value)}`}</Text>
		),
	}
})

jest.mock('../../components/SectionHeader', () => {
	const React = require('react')
	const { Text } = require('react-native')
	return {
		SectionHeader: ({ title }: { title: string }) => <Text>{title}</Text>,
	}
})

jest.mock('../../components/PrimaryButton', () => {
	const React = require('react')
	const { Text, TouchableOpacity } = require('react-native')
	return {
		PrimaryButton: ({
			label,
			onPress,
		}: {
			label: string
			onPress: () => void
		}) => (
			<TouchableOpacity onPress={onPress}>
				<Text>{label}</Text>
			</TouchableOpacity>
		),
	}
})

jest.mock('../../components/SecondaryButton', () => {
	const React = require('react')
	const { Text, TouchableOpacity } = require('react-native')
	return {
		SecondaryButton: ({ label, onPress }: { label: string; onPress: () => void }) => (
			<TouchableOpacity onPress={onPress}>
				<Text>{label}</Text>
			</TouchableOpacity>
		),
	}
})

jest.mock('../../context/AuthContext', () => ({
	useAuth: () => ({
		user: { id: 'user-1', email: 'user@example.com' },
		logout: mockLogout,
	}),
}))

jest.mock('../../context/ProfileContext', () => ({
	useProfile: () => mockProfileState,
}))

jest.mock('../../services/api.service', () => ({
	apiService: {
		getUserStats: jest.fn(),
		getUserStreak: jest.fn(),
		exportUserData: jest.fn(),
		deleteAccount: jest.fn(),
	},
}))

jest.mock('../../services/storage.service', () => ({
	storageService: {
		clearAllData: jest.fn(),
	},
}))

jest.mock('../../services/email.service', () => ({
	emailService: {
		sendDataExportEmail: jest.fn(),
	},
}))

jest.mock('../../utils/hapticFeedback', () => ({
	hapticFeedback: {
		selection: jest.fn(),
		success: jest.fn(),
	},
}))

describe('ProfileScreen', () => {
	beforeEach(() => {
		mockRefresh.mockClear()
		mockRefreshStats.mockClear()
		mockUpdateProfile.mockClear()
		mockUpdatePreferences.mockClear()
		mockLogout.mockClear()
		mockProfileState.stats = {
			totalSessions: 17,
			bestScore: 92,
			currentStreak: 8,
		}
		mockProfileState.preferences = {
			notifications_enabled: true,
			dark_mode_enabled: true,
			analytics_enabled: true,
		}
		mockProfileState.profile = {
			id: 'user-1',
			name: 'Task Six User',
			username: 'task6',
			position: 'Guard',
			skill_level: 'advanced',
			profile: {
				notifications_enabled: true,
				dark_mode_enabled: true,
				analytics_enabled: true,
			},
		}
		mockProfileState.profileLoading = false
		mockProfileState.statsLoading = false
		mockProfileState.profileError = null
		mockProfileState.statsError = null
	})

	test('uses context/api-backed stats for authenticated user flow', async () => {
		const { apiService } = require('../../services/api.service')
		render(<ProfileScreen />)

		await waitFor(() => {
			expect(mockRefreshStats).toHaveBeenCalledTimes(1)
		})

		expect(apiService.getUserStats).not.toHaveBeenCalled()
		expect(apiService.getUserStreak).not.toHaveBeenCalled()
		expect(mockRefresh).not.toHaveBeenCalled()
		expect(mockUpdatePreferences).not.toHaveBeenCalled()
	})

	test('preference toggle persists through profile context path', async () => {
		const { getByLabelText } = render(<ProfileScreen />)

		fireEvent(getByLabelText('Dark mode'), 'valueChange', false)

		await waitFor(() => {
			expect(mockUpdatePreferences).toHaveBeenCalledWith({ dark_mode_enabled: false })
		})
	})

	test('renders safe fallbacks for partial profile data', () => {
		mockProfileState.profile = {
			id: 'user-1',
			name: null,
			username: null,
			position: null,
			skill_level: null,
			profile: null,
		}

		const { getByText } = render(<ProfileScreen />)

		expect(getByText('P')).toBeTruthy()
		expect(getByText('Profile unavailable')).toBeTruthy()
	})

	test('shows retry banner and refreshes on retry press', async () => {
		mockProfileState.profileError = 'Profile service returned malformed payload.'
		const { getByText } = render(<ProfileScreen />)

		fireEvent.press(getByText('Retry'))

		await waitFor(() => {
			expect(mockRefresh).toHaveBeenCalledTimes(1)
		})
	})

	test('shows transient toast for offline profile errors', () => {
		mockProfileState.profileError = 'No internet connection. Showing last synced profile data.'
		const { getByTestId, queryByText, getByText } = render(<ProfileScreen />)

		expect(getByTestId('profile-network-toast')).toBeTruthy()
		expect(getByText('No internet connection. Showing last synced profile data.')).toBeTruthy()
		expect(queryByText('Retry')).toBeNull()
	})

	test('edits profile name and reflects saved value in UI', async () => {
		const updatedName = 'Task Eight User'

		mockUpdateProfile.mockImplementationOnce(async (payload: any) => {
			mockProfileState.profile = {
				...mockProfileState.profile,
				name: payload.name,
				position: payload.position,
				skill_level: payload.skillLevel,
			}
			return {}
		})

		const { getByText, getByPlaceholderText } = render(<ProfileScreen />)

		fireEvent.press(getByText('Edit Profile'))
		fireEvent.changeText(getByPlaceholderText('Your name'), updatedName)
		fireEvent.press(getByText('Save'))

		await waitFor(() => {
			expect(mockUpdateProfile).toHaveBeenCalledWith(expect.objectContaining({ name: updatedName }))
		})
		await waitFor(() => {
			expect(mockRefresh).toHaveBeenCalledTimes(1)
		})
		await waitFor(() => {
			expect(getByText(updatedName)).toBeTruthy()
		})
	})
})
