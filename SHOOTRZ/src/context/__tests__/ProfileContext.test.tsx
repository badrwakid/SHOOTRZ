import React from 'react'
import { Text } from 'react-native'
import { act, render, screen, waitFor } from '@testing-library/react-native'
import { ProfileProvider, useProfile } from '../ProfileContext'
import { apiService } from '../../services/api.service'
import { eventBus } from '../../utils/eventBus'

function createDeferred<T>() {
	let resolve!: (value: T | PromiseLike<T>) => void
	let reject!: (reason?: unknown) => void
	const promise = new Promise<T>((res, rej) => {
		resolve = res
		reject = rej
	})
	return { promise, resolve, reject }
}

const mockSetUser = jest.fn()
let mockAuthUser = {
	id: 'user-1',
	name: 'Old Name',
	username: 'old-user',
	position: 'Guard',
	skillLevel: 'beginner',
}
const mockAuthState = {
	user: mockAuthUser,
	setUser: mockSetUser,
}

jest.mock('../AuthContext', () => ({
	useAuth: () => mockAuthState,
}))

jest.mock('../../services/api.service', () => ({
	apiService: {
		getUserProfile: jest.fn(),
		getUserStats: jest.fn(),
		getUserStreak: jest.fn(),
		updateUserProfile: jest.fn(),
		updateUserPreferences: jest.fn(),
	},
}))

describe('ProfileContext', () => {
	beforeEach(() => {
		mockSetUser.mockReset()
		mockAuthUser = {
			id: 'user-1',
			name: 'Old Name',
			username: 'old-user',
			position: 'Guard',
			skillLevel: 'beginner',
		}
		mockAuthState.user = mockAuthUser
		;(apiService.getUserProfile as jest.Mock).mockReset()
		;(apiService.getUserStats as jest.Mock).mockReset()
		;(apiService.getUserStreak as jest.Mock).mockReset()
		;(apiService.updateUserProfile as jest.Mock).mockReset()
		;(apiService.updateUserPreferences as jest.Mock).mockReset()
	})

	test('refresh loads profile, stats, and preferences from api', async () => {
		;(apiService.getUserProfile as jest.Mock).mockResolvedValue({
			id: 'user-1',
			name: 'A',
			profile: {
				notifications_enabled: true,
				dark_mode_enabled: false,
				analytics_enabled: true,
			},
		})
		;(apiService.getUserStats as jest.Mock).mockResolvedValue({
			totalSessions: 9,
			bestScore: 83.2,
		})
		;(apiService.getUserStreak as jest.Mock).mockResolvedValue({
			currentStreak: 4,
		})

		function Probe(): React.JSX.Element {
			const p = useProfile()
			return (
				<>
					<Text testID="name">{p.profile?.name ?? 'none'}</Text>
					<Text testID="sessions">{String(p.stats.totalSessions)}</Text>
					<Text testID="best">{String(p.stats.bestScore)}</Text>
					<Text testID="streak">{String(p.stats.currentStreak)}</Text>
					<Text testID="dark">{String(p.preferences.dark_mode_enabled)}</Text>
				</>
			)
		}

		render(
			<ProfileProvider>
				<Probe />
			</ProfileProvider>,
		)

		await waitFor(() => {
			expect(apiService.getUserProfile).toHaveBeenCalledTimes(1)
			expect(apiService.getUserStats).toHaveBeenCalledTimes(1)
			expect(apiService.getUserStreak).toHaveBeenCalledTimes(1)
		})

		await waitFor(() => {
			expect(screen.getByTestId('name').props.children).toBe('A')
			expect(screen.getByTestId('sessions').props.children).toBe('9')
			expect(screen.getByTestId('best').props.children).toBe('83')
			expect(screen.getByTestId('streak').props.children).toBe('4')
			expect(screen.getByTestId('dark').props.children).toBe('false')
		})
	})

	test('keeps profile stable within ttl and invalidates on user updated event', async () => {
		;(apiService.getUserProfile as jest.Mock).mockResolvedValue({
			id: 'user-1',
			name: 'TTL User',
			profile: {},
		})
		;(apiService.getUserStats as jest.Mock).mockResolvedValue({
			totalSessions: 5,
			bestScore: 78.4,
		})
		;(apiService.getUserStreak as jest.Mock).mockResolvedValue({
			currentStreak: 3,
		})

		function Probe(): React.JSX.Element {
			const p = useProfile()
			return <Text testID="name">{p.profile?.name ?? 'none'}</Text>
		}

		const { rerender } = render(
			<ProfileProvider>
				<Probe />
			</ProfileProvider>,
		)

		await waitFor(() => {
			expect(apiService.getUserProfile).toHaveBeenCalledTimes(1)
		})

		rerender(
			<ProfileProvider>
				<Probe />
			</ProfileProvider>,
		)

		await waitFor(() => {
			expect(screen.getByTestId('name').props.children).toBe('TTL User')
		})
		expect(apiService.getUserProfile).toHaveBeenCalledTimes(1)

		await act(async () => {
			eventBus.emit('user:updated')
		})

		await waitFor(() => {
			expect(apiService.getUserProfile).toHaveBeenCalledTimes(2)
		})
	})

	test('updates profile centrally and emits invalidation event', async () => {
		;(apiService.getUserProfile as jest.Mock).mockResolvedValue({
			id: 'user-1',
			name: 'Initial',
			profile: {},
		})
		;(apiService.getUserStats as jest.Mock).mockResolvedValue({
			totalSessions: 1,
			bestScore: 60,
		})
		;(apiService.getUserStreak as jest.Mock).mockResolvedValue({
			currentStreak: 1,
		})
		;(apiService.updateUserProfile as jest.Mock).mockResolvedValue({
			id: 'user-1',
			name: 'Updated Name',
			username: 'new-user',
			position: 'Forward',
			skill_level: 'advanced',
			profile: {},
		})

		const emitSpy = jest.spyOn(eventBus, 'emit')
		let updateProfileFn: ReturnType<typeof useProfile>['updateProfile'] | null = null

		function Probe(): React.JSX.Element {
			const p = useProfile()
			updateProfileFn = p.updateProfile
			return <Text testID="name">{p.profile?.name ?? 'none'}</Text>
		}

		render(
			<ProfileProvider>
				<Probe />
			</ProfileProvider>,
		)

		await waitFor(() => {
			expect(apiService.getUserProfile).toHaveBeenCalledTimes(1)
		})

		await act(async () => {
			expect(updateProfileFn).not.toBeNull()
			await (updateProfileFn as ReturnType<typeof useProfile>['updateProfile'])({
				name: 'Updated Name',
			} as any)
		})

		await waitFor(() => {
			expect(screen.getByTestId('name').props.children).toBe('Updated Name')
		})
		expect(emitSpy).toHaveBeenCalledWith('user:updated')
		expect(mockSetUser).toHaveBeenCalled()
		emitSpy.mockRestore()
	})

	test('refreshStats always fetches fresh server stats', async () => {
		;(apiService.getUserProfile as jest.Mock).mockResolvedValue({
			id: 'user-1',
			name: 'Player',
			profile: {},
		})
		;(apiService.getUserStats as jest.Mock).mockResolvedValue({
			totalSessions: 2,
			bestScore: 61,
		})
		;(apiService.getUserStreak as jest.Mock).mockResolvedValue({
			currentStreak: 1,
		})

		let refreshStatsFn: ReturnType<typeof useProfile>['refreshStats'] | null = null

		function Probe(): React.JSX.Element {
			const p = useProfile()
			refreshStatsFn = p.refreshStats
			return <Text testID="sessions">{String(p.stats.totalSessions)}</Text>
		}

		render(
			<ProfileProvider>
				<Probe />
			</ProfileProvider>,
		)

		await waitFor(() => {
			expect(apiService.getUserStats).toHaveBeenCalledTimes(1)
		})

		await act(async () => {
			expect(refreshStatsFn).not.toBeNull()
			await (refreshStatsFn as ReturnType<typeof useProfile>['refreshStats'])()
			await (refreshStatsFn as ReturnType<typeof useProfile>['refreshStats'])()
		})

		expect(apiService.getUserStats).toHaveBeenCalledTimes(3)
		expect(apiService.getUserStreak).toHaveBeenCalledTimes(3)
	})

	test('updatePreferences applies optimistic value then reconciles with server profile', async () => {
		;(apiService.getUserProfile as jest.Mock)
			.mockResolvedValueOnce({
				id: 'user-1',
				name: 'Player',
				profile: {
					notifications_enabled: true,
					dark_mode_enabled: true,
					analytics_enabled: true,
				},
			})
			.mockResolvedValueOnce({
				id: 'user-1',
				name: 'Player',
				profile: {
					notifications_enabled: false,
					dark_mode_enabled: false,
					analytics_enabled: true,
				},
			})
		;(apiService.getUserStats as jest.Mock).mockResolvedValue({
			totalSessions: 1,
			bestScore: 50,
		})
		;(apiService.getUserStreak as jest.Mock).mockResolvedValue({
			currentStreak: 1,
		})
		let resolveUpdate: (() => void) | null = null
		;(apiService.updateUserPreferences as jest.Mock).mockImplementation(
			() => new Promise<void>(resolve => {
				resolveUpdate = resolve
			}),
		)

		let updatePreferencesFn: ReturnType<typeof useProfile>['updatePreferences'] | null = null

		function Probe(): React.JSX.Element {
			const p = useProfile()
			updatePreferencesFn = p.updatePreferences
			return <Text testID="dark">{String(p.preferences.dark_mode_enabled)}</Text>
		}

		render(
			<ProfileProvider>
				<Probe />
			</ProfileProvider>,
		)

		await waitFor(() => {
			expect(screen.getByTestId('dark').props.children).toBe('true')
		})

		let updatePromise: Promise<unknown> | null = null
		await act(async () => {
			expect(updatePreferencesFn).not.toBeNull()
			updatePromise = (updatePreferencesFn as ReturnType<typeof useProfile>['updatePreferences'])({
				dark_mode_enabled: false,
			})
		})

		expect(screen.getByTestId('dark').props.children).toBe('false')

		await act(async () => {
			expect(resolveUpdate).not.toBeNull()
			;(resolveUpdate as () => void)()
			await updatePromise
		})

		expect(apiService.updateUserPreferences).toHaveBeenCalledWith({ dark_mode_enabled: false })
		expect(screen.getByTestId('dark').props.children).toBe('false')
		expect(apiService.getUserProfile).toHaveBeenCalledTimes(2)
	})

	test('updatePreferences rolls back optimistic value when persistence fails', async () => {
		;(apiService.getUserProfile as jest.Mock).mockResolvedValue({
			id: 'user-1',
			name: 'Player',
			profile: {
				notifications_enabled: true,
				dark_mode_enabled: true,
				analytics_enabled: true,
			},
		})
		;(apiService.getUserStats as jest.Mock).mockResolvedValue({
			totalSessions: 1,
			bestScore: 50,
		})
		;(apiService.getUserStreak as jest.Mock).mockResolvedValue({
			currentStreak: 1,
		})
		;(apiService.updateUserPreferences as jest.Mock).mockRejectedValue(new Error('network failed'))

		let updatePreferencesFn: ReturnType<typeof useProfile>['updatePreferences'] | null = null

		function Probe(): React.JSX.Element {
			const p = useProfile()
			updatePreferencesFn = p.updatePreferences
			return <Text testID="dark">{String(p.preferences.dark_mode_enabled)}</Text>
		}

		render(
			<ProfileProvider>
				<Probe />
			</ProfileProvider>,
		)

		await waitFor(() => {
			expect(screen.getByTestId('dark').props.children).toBe('true')
		})

		await act(async () => {
			await expect(
				(updatePreferencesFn as ReturnType<typeof useProfile>['updatePreferences'])({
					dark_mode_enabled: false,
				}),
			).rejects.toThrow('No internet connection')
		})

		expect(screen.getByTestId('dark').props.children).toBe('true')
		expect(apiService.getUserProfile).toHaveBeenCalledTimes(1)
	})

	test('updatePreferences rollback uses latest pre-update snapshot', async () => {
		;(apiService.getUserProfile as jest.Mock)
			.mockResolvedValueOnce({
				id: 'user-1',
				name: 'Player',
				profile: {
					notifications_enabled: true,
					dark_mode_enabled: true,
					analytics_enabled: true,
				},
			})
			.mockResolvedValueOnce({
				id: 'user-1',
				name: 'Player',
				profile: {
					notifications_enabled: true,
					dark_mode_enabled: false,
					analytics_enabled: true,
				},
			})
			.mockResolvedValueOnce({
				id: 'user-1',
				name: 'Player',
				profile: {
					notifications_enabled: true,
					dark_mode_enabled: false,
					analytics_enabled: true,
				},
			})
		;(apiService.getUserStats as jest.Mock).mockResolvedValue({
			totalSessions: 1,
			bestScore: 50,
		})
		;(apiService.getUserStreak as jest.Mock).mockResolvedValue({
			currentStreak: 1,
		})
		;(apiService.updateUserPreferences as jest.Mock)
			.mockResolvedValueOnce(undefined)
			.mockRejectedValueOnce(new Error('network failed'))

		let updatePreferencesFn: ReturnType<typeof useProfile>['updatePreferences'] | null = null

		function Probe(): React.JSX.Element {
			const p = useProfile()
			updatePreferencesFn = p.updatePreferences
			return (
				<>
					<Text testID="dark">{String(p.preferences.dark_mode_enabled)}</Text>
					<Text testID="notifications">{String(p.preferences.notifications_enabled)}</Text>
				</>
			)
		}

		render(
			<ProfileProvider>
				<Probe />
			</ProfileProvider>,
		)

		await waitFor(() => {
			expect(screen.getByTestId('dark').props.children).toBe('true')
		})

		await act(async () => {
			await (updatePreferencesFn as ReturnType<typeof useProfile>['updatePreferences'])({
				dark_mode_enabled: false,
			})
		})

		expect(screen.getByTestId('dark').props.children).toBe('false')

		await act(async () => {
			await expect(
				(updatePreferencesFn as ReturnType<typeof useProfile>['updatePreferences'])({
					notifications_enabled: false,
				}),
			).rejects.toThrow('No internet connection')
		})

		expect(screen.getByTestId('dark').props.children).toBe('false')
		expect(screen.getByTestId('notifications').props.children).toBe('true')
	})

	test('uses safe defaults when profile payload is partial or null', async () => {
		;(apiService.getUserProfile as jest.Mock).mockResolvedValue({
			id: 'user-1',
			name: null,
			profile: null,
		})
		;(apiService.getUserStats as jest.Mock).mockResolvedValue({})
		;(apiService.getUserStreak as jest.Mock).mockResolvedValue({})

		function Probe(): React.JSX.Element {
			const p = useProfile()
			return (
				<>
					<Text testID="name">{String(p.profile?.name ?? 'none')}</Text>
					<Text testID="sessions">{String(p.stats.totalSessions)}</Text>
					<Text testID="best">{String(p.stats.bestScore)}</Text>
					<Text testID="streak">{String(p.stats.currentStreak)}</Text>
					<Text testID="notifications">{String(p.preferences.notifications_enabled)}</Text>
					<Text testID="dark">{String(p.preferences.dark_mode_enabled)}</Text>
					<Text testID="analytics">{String(p.preferences.analytics_enabled)}</Text>
				</>
			)
		}

		render(
			<ProfileProvider>
				<Probe />
			</ProfileProvider>,
		)

		await waitFor(() => {
			expect(screen.getByTestId('name').props.children).toBe('none')
			expect(screen.getByTestId('sessions').props.children).toBe('0')
			expect(screen.getByTestId('best').props.children).toBe('0')
			expect(screen.getByTestId('streak').props.children).toBe('0')
			expect(screen.getByTestId('notifications').props.children).toBe('true')
			expect(screen.getByTestId('dark').props.children).toBe('true')
			expect(screen.getByTestId('analytics').props.children).toBe('true')
		})
	})

	test('keeps last snapshot and reports offline-safe errors on network failures', async () => {
		;(apiService.getUserProfile as jest.Mock)
			.mockResolvedValueOnce({
				id: 'user-1',
				name: 'Online Player',
				profile: {
					notifications_enabled: true,
					dark_mode_enabled: false,
					analytics_enabled: true,
				},
			})
			.mockRejectedValueOnce({ code: 'ERR_NETWORK', message: 'request failed' })
		;(apiService.getUserStats as jest.Mock)
			.mockResolvedValueOnce({
				totalSessions: 9,
				bestScore: 82,
			})
			.mockRejectedValueOnce({ code: 'ERR_NETWORK', message: 'request failed' })
		;(apiService.getUserStreak as jest.Mock)
			.mockResolvedValueOnce({
				currentStreak: 3,
			})
			.mockRejectedValueOnce({ code: 'ERR_NETWORK', message: 'request failed' })

		let refreshFn: ReturnType<typeof useProfile>['refresh'] | null = null

		function Probe(): React.JSX.Element {
			const p = useProfile()
			refreshFn = p.refresh
			return (
				<>
					<Text testID="name">{String(p.profile?.name ?? 'none')}</Text>
					<Text testID="sessions">{String(p.stats.totalSessions)}</Text>
					<Text testID="profileError">{String(p.profileError ?? '')}</Text>
					<Text testID="statsError">{String(p.statsError ?? '')}</Text>
				</>
			)
		}

		render(
			<ProfileProvider>
				<Probe />
			</ProfileProvider>,
		)

		await waitFor(() => {
			expect(screen.getByTestId('name').props.children).toBe('Online Player')
			expect(screen.getByTestId('sessions').props.children).toBe('9')
		})

		await act(async () => {
			await (refreshFn as ReturnType<typeof useProfile>['refresh'])()
		})

		expect(screen.getByTestId('name').props.children).toBe('Online Player')
		expect(screen.getByTestId('sessions').props.children).toBe('9')
		expect(screen.getByTestId('profileError').props.children).toContain('No internet connection')
		expect(screen.getByTestId('statsError').props.children).toContain('No internet connection')
	})

	test('ignores stale responses from previous user after account switch', async () => {
		const user1Profile = createDeferred<any>()
		const user2Profile = createDeferred<any>()
		const user1Stats = createDeferred<any>()
		const user2Stats = createDeferred<any>()
		const user1Streak = createDeferred<any>()
		const user2Streak = createDeferred<any>()

		;(apiService.getUserProfile as jest.Mock)
			.mockReturnValueOnce(user1Profile.promise)
			.mockReturnValueOnce(user2Profile.promise)
		;(apiService.getUserStats as jest.Mock)
			.mockReturnValueOnce(user1Stats.promise)
			.mockReturnValueOnce(user2Stats.promise)
		;(apiService.getUserStreak as jest.Mock)
			.mockReturnValueOnce(user1Streak.promise)
			.mockReturnValueOnce(user2Streak.promise)

		function Probe(): React.JSX.Element {
			const p = useProfile()
			return <Text testID="name">{p.profile?.name ?? 'none'}</Text>
		}

		const view = render(
			<ProfileProvider>
				<Probe />
			</ProfileProvider>,
		)

		mockAuthUser = {
			id: 'user-2',
			name: 'User Two',
			username: 'user-2',
			position: 'Center',
			skillLevel: 'advanced',
		}
		mockAuthState.user = mockAuthUser

		view.rerender(
			<ProfileProvider>
				<Probe />
			</ProfileProvider>,
		)

		await act(async () => {
			user2Profile.resolve({ id: 'user-2', name: 'Fresh User', profile: {} })
			user2Stats.resolve({ totalSessions: 20, bestScore: 95 })
			user2Streak.resolve({ currentStreak: 7 })
			await Promise.resolve()
		})

		await waitFor(() => {
			expect(screen.getByTestId('name').props.children).toBe('Fresh User')
		})

		await act(async () => {
			user1Profile.resolve({ id: 'user-1', name: 'Leaked User', profile: {} })
			user1Stats.resolve({ totalSessions: 1, bestScore: 10 })
			user1Streak.resolve({ currentStreak: 1 })
			await Promise.resolve()
		})

		expect(screen.getByTestId('name').props.children).toBe('Fresh User')
	})

	test('Profile loads correctly', async () => {
		;(apiService.getUserProfile as jest.Mock).mockResolvedValue({
			id: 'user-1',
			name: 'Loaded User',
			profile: {
				notifications_enabled: true,
				dark_mode_enabled: false,
				analytics_enabled: true,
			},
		})
		;(apiService.getUserStats as jest.Mock).mockResolvedValue({
			totalSessions: 12,
			bestScore: 88,
		})
		;(apiService.getUserStreak as jest.Mock).mockResolvedValue({
			currentStreak: 6,
		})

		function Probe(): React.JSX.Element {
			const p = useProfile()
			return (
				<>
					<Text testID="name">{p.profile?.name ?? 'none'}</Text>
					<Text testID="sessions">{String(p.stats.totalSessions)}</Text>
					<Text testID="streak">{String(p.stats.currentStreak)}</Text>
					<Text testID="dark">{String(p.preferences.dark_mode_enabled)}</Text>
				</>
			)
		}

		render(
			<ProfileProvider>
				<Probe />
			</ProfileProvider>,
		)

		await waitFor(() => {
			expect(screen.getByTestId('name').props.children).toBe('Loaded User')
			expect(screen.getByTestId('sessions').props.children).toBe('12')
			expect(screen.getByTestId('streak').props.children).toBe('6')
			expect(screen.getByTestId('dark').props.children).toBe('false')
		})
	})

	test('Edit updates UI instantly', async () => {
		;(apiService.getUserProfile as jest.Mock).mockResolvedValue({
			id: 'user-1',
			name: 'Before Edit',
			profile: {},
		})
		;(apiService.getUserStats as jest.Mock).mockResolvedValue({
			totalSessions: 1,
			bestScore: 50,
		})
		;(apiService.getUserStreak as jest.Mock).mockResolvedValue({
			currentStreak: 1,
		})
		;(apiService.updateUserProfile as jest.Mock).mockResolvedValue({
			id: 'user-1',
			name: 'After Edit',
			profile: {},
		})

		let updateProfileFn: ReturnType<typeof useProfile>['updateProfile'] | null = null

		function Probe(): React.JSX.Element {
			const p = useProfile()
			updateProfileFn = p.updateProfile
			return <Text testID="name">{p.profile?.name ?? 'none'}</Text>
		}

		render(
			<ProfileProvider>
				<Probe />
			</ProfileProvider>,
		)

		await waitFor(() => {
			expect(screen.getByTestId('name').props.children).toBe('Before Edit')
		})

		await act(async () => {
			await (updateProfileFn as ReturnType<typeof useProfile>['updateProfile'])({
				name: 'After Edit',
			} as any)
		})

		expect(screen.getByTestId('name').props.children).toBe('After Edit')
	})

	test('Toggles persist after refresh', async () => {
		const persistedProfile = {
			id: 'user-1',
			name: 'Player',
			profile: {
				notifications_enabled: true,
				dark_mode_enabled: false,
				analytics_enabled: true,
			},
		}
		;(apiService.getUserProfile as jest.Mock)
			.mockResolvedValue(persistedProfile)
			.mockResolvedValueOnce({
				id: 'user-1',
				name: 'Player',
				profile: {
					notifications_enabled: true,
					dark_mode_enabled: true,
					analytics_enabled: true,
				},
			})
		;(apiService.getUserStats as jest.Mock).mockResolvedValue({
			totalSessions: 3,
			bestScore: 70,
		})
		;(apiService.getUserStreak as jest.Mock).mockResolvedValue({
			currentStreak: 2,
		})
		;(apiService.updateUserPreferences as jest.Mock).mockResolvedValue(undefined)

		let updatePreferencesFn: ReturnType<typeof useProfile>['updatePreferences'] | null = null
		let refreshFn: ReturnType<typeof useProfile>['refresh'] | null = null

		function Probe(): React.JSX.Element {
			const p = useProfile()
			updatePreferencesFn = p.updatePreferences
			refreshFn = p.refresh
			return <Text testID="dark">{String(p.preferences.dark_mode_enabled)}</Text>
		}

		render(
			<ProfileProvider>
				<Probe />
			</ProfileProvider>,
		)

		await waitFor(() => {
			expect(screen.getByTestId('dark').props.children).toBe('true')
		})

		await act(async () => {
			await (updatePreferencesFn as ReturnType<typeof useProfile>['updatePreferences'])({
				dark_mode_enabled: false,
			})
		})

		expect(screen.getByTestId('dark').props.children).toBe('false')

		await act(async () => {
			await (refreshFn as ReturnType<typeof useProfile>['refresh'])()
		})

		await waitFor(() => {
			expect(screen.getByTestId('dark').props.children).toBe('false')
		})
		expect(apiService.updateUserPreferences).toHaveBeenCalledWith({ dark_mode_enabled: false })
	})
})
