import React, {
	createContext,
	useCallback,
	useContext,
	useEffect,
	useMemo,
	useRef,
	useState,
} from 'react'
import { apiService } from '../services/api.service'
import { useAuth } from './AuthContext'
import { eventBus } from '../utils/eventBus'
import type {
	UserProfile,
	UserProfileResponse,
	UserPreferencesPayload,
} from '../types/contracts'

const PROFILE_TTL_MS = 30_000

function isNetworkError(error: any): boolean {
	if (!error) {
		return false
	}
	const code = typeof error.code === 'string' ? error.code.toUpperCase() : ''
	const message = typeof error.message === 'string' ? error.message.toLowerCase() : ''
	return code === 'ERR_NETWORK'
		|| code === 'ECONNABORTED'
		|| message.includes('network')
		|| message.includes('timeout')
		|| message.includes('failed to fetch')
}

function getSafeErrorMessage(error: any, fallback: string): string {
	if (isNetworkError(error)) {
		return 'No internet connection. Showing last synced profile data.'
	}
	return error?.message || fallback
}

function toSafeNumber(value: unknown, fallback = 0): number {
	return Number.isFinite(value) ? Number(value) : fallback
}

interface ProfileStats {
	totalSessions: number
	bestScore: number
	currentStreak: number
}

interface ProfilePreferences {
	notifications_enabled: boolean
	dark_mode_enabled: boolean
	analytics_enabled: boolean
}

interface ProfileContextValue {
	profile: UserProfileResponse | null
	stats: ProfileStats
	preferences: ProfilePreferences
	profileLoading: boolean
	statsLoading: boolean
	profileError: string | null
	statsError: string | null
	refresh: () => Promise<void>
	refreshStats: () => Promise<void>
	updateProfile: (payload: Partial<UserProfile>) => Promise<UserProfileResponse>
	updatePreferences: (payload: UserPreferencesPayload) => Promise<UserProfileResponse>
}

const defaultStats: ProfileStats = {
	totalSessions: 0,
	bestScore: 0,
	currentStreak: 0,
}

const defaultPreferences: ProfilePreferences = {
	notifications_enabled: true,
	dark_mode_enabled: true,
	analytics_enabled: true,
}

const ProfileCtx = createContext<ProfileContextValue | null>(null)

export const ProfileProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
	const { user, setUser } = useAuth()
	const [profile, setProfile] = useState<UserProfileResponse | null>(null)
	const [stats, setStats] = useState<ProfileStats>(defaultStats)
	const [preferences, setPreferences] = useState<ProfilePreferences>(defaultPreferences)
	const [profileLoading, setProfileLoading] = useState(false)
	const [statsLoading, setStatsLoading] = useState(false)
	const [profileError, setProfileError] = useState<string | null>(null)
	const [statsError, setStatsError] = useState<string | null>(null)
	const lastFetchedAtRef = useRef(0)
	const lastUserIdRef = useRef<string | null | undefined>(user?.id)
	const skipNextUserUpdatedRef = useRef(false)
	const profileRequestIdRef = useRef(0)
	const statsRequestIdRef = useRef(0)

	const applyProfile = useCallback((nextProfile: UserProfileResponse | null) => {
		setProfile(nextProfile)
		const serverPrefs = nextProfile?.profile ?? {}
		setPreferences({
			notifications_enabled: serverPrefs.notifications_enabled ?? true,
			dark_mode_enabled: serverPrefs.dark_mode_enabled ?? true,
			analytics_enabled: serverPrefs.analytics_enabled ?? true,
		})
	}, [])

	const syncAuthUser = useCallback((nextProfile: UserProfileResponse | null) => {
		if (!nextProfile || !user) {
			return
		}
		const skillLevel = typeof nextProfile.skill_level === 'string'
			&& ['beginner', 'intermediate', 'advanced'].includes(nextProfile.skill_level)
			? (nextProfile.skill_level as 'beginner' | 'intermediate' | 'advanced')
			: user.skillLevel
		const nextUser = {
			...user,
			name: typeof nextProfile.name === 'string' ? nextProfile.name : user.name,
			username: typeof nextProfile.username === 'string'
				? nextProfile.username
				: user.username,
			position: typeof nextProfile.position === 'string'
				? nextProfile.position
				: user.position,
			skillLevel,
		}
		if (
			nextUser.name === user.name
			&& nextUser.username === user.username
			&& nextUser.position === user.position
			&& nextUser.skillLevel === user.skillLevel
		) {
			return
		}
		setUser(nextUser)
	}, [setUser, user])

	const refreshStats = useCallback(async () => {
		const userId = user?.id
		if (!userId) {
			setStats(defaultStats)
			setStatsError(null)
			return
		}
		const requestId = ++statsRequestIdRef.current
		setStatsLoading(true)
		setStatsError(null)
		try {
			const [serverStats, serverStreak] = await Promise.all([
				apiService.getUserStats(),
				apiService.getUserStreak(),
			])
			if (requestId !== statsRequestIdRef.current || userId !== lastUserIdRef.current) {
				return
			}
			setStats({
				totalSessions: toSafeNumber(serverStats?.totalSessions),
				bestScore: Math.round(toSafeNumber(serverStats?.bestScore)),
				currentStreak: toSafeNumber(serverStreak?.currentStreak),
			})
		} catch (error: any) {
			if (requestId !== statsRequestIdRef.current || userId !== lastUserIdRef.current) {
				return
			}
			setStatsError(getSafeErrorMessage(error, 'Failed to load stats from server.'))
		} finally {
			if (requestId === statsRequestIdRef.current && userId === lastUserIdRef.current) {
				setStatsLoading(false)
			}
		}
	}, [user?.id])

	const refreshProfile = useCallback(async (options?: { force?: boolean }) => {
		const userId = user?.id
		if (!userId) {
			applyProfile(null)
			setProfileError(null)
			return
		}
		const force = Boolean(options?.force)
		const age = Date.now() - lastFetchedAtRef.current
		if (!force && lastFetchedAtRef.current > 0 && age < PROFILE_TTL_MS) {
			return
		}
		const requestId = ++profileRequestIdRef.current
		setProfileLoading(true)
		setProfileError(null)
		try {
			const nextProfile = await apiService.getUserProfile()
			if (requestId !== profileRequestIdRef.current || userId !== lastUserIdRef.current) {
				return
			}
			applyProfile(nextProfile)
			syncAuthUser(nextProfile)
			lastFetchedAtRef.current = Date.now()
		} catch (error: any) {
			if (requestId !== profileRequestIdRef.current || userId !== lastUserIdRef.current) {
				return
			}
			setProfileError(getSafeErrorMessage(error, 'Failed to load profile from server.'))
		} finally {
			if (requestId === profileRequestIdRef.current && userId === lastUserIdRef.current) {
				setProfileLoading(false)
			}
		}
	}, [applyProfile, syncAuthUser, user?.id])

	const refresh = useCallback(async () => {
		await Promise.all([
			refreshProfile({ force: true }),
			refreshStats(),
		])
	}, [refreshProfile, refreshStats])

	const updateProfile = useCallback(async (
		payload: Partial<UserProfile>,
	): Promise<UserProfileResponse> => {
		const response = await apiService.updateUserProfile(payload)
		const merged = response as UserProfileResponse
		applyProfile(merged)
		syncAuthUser(merged)
		lastFetchedAtRef.current = 0
		skipNextUserUpdatedRef.current = true
		eventBus.emit('user:updated')
		return merged
	}, [applyProfile, preferences, syncAuthUser])

	const updatePreferences = useCallback(async (
		payload: UserPreferencesPayload,
	): Promise<UserProfileResponse> => {
		const previousPreferences = { ...preferences }
		setPreferences(prev => ({
			...prev,
			...payload,
		}))
		try {
			await apiService.updateUserPreferences(payload)
			const profileResponse = await apiService.getUserProfile()
			const merged = profileResponse as UserProfileResponse
			applyProfile(merged)
			syncAuthUser(merged)
			lastFetchedAtRef.current = 0
			skipNextUserUpdatedRef.current = true
			eventBus.emit('user:updated')
			return merged
		} catch (error) {
			setPreferences(previousPreferences)
			throw new Error(getSafeErrorMessage(error, 'Failed to save preferences.'))
		}
	}, [applyProfile, preferences, syncAuthUser])

	useEffect(() => {
		if (lastUserIdRef.current !== user?.id) {
			lastUserIdRef.current = user?.id
			profileRequestIdRef.current += 1
			statsRequestIdRef.current += 1
			lastFetchedAtRef.current = 0
			applyProfile(null)
			setStats(defaultStats)
			setProfileError(null)
			setStatsError(null)
			setProfileLoading(false)
			setStatsLoading(false)
		}
	}, [applyProfile, user?.id])

	useEffect(() => {
		if (!user?.id) {
			return
		}
		void refresh()
	}, [refresh, user?.id])

	useEffect(() => {
		const unsubscribe = eventBus.on('user:updated', () => {
			if (skipNextUserUpdatedRef.current) {
				skipNextUserUpdatedRef.current = false
				return
			}
			lastFetchedAtRef.current = 0
			void refresh()
		})
		return unsubscribe
	}, [refresh])

	const value = useMemo<ProfileContextValue>(() => ({
		profile,
		stats,
		preferences,
		profileLoading,
		statsLoading,
		profileError,
		statsError,
		refresh,
		refreshStats,
		updateProfile,
		updatePreferences,
	}), [
		profile,
		stats,
		preferences,
		profileLoading,
		statsLoading,
		profileError,
		statsError,
		refresh,
		refreshStats,
		updateProfile,
		updatePreferences,
	])

	return <ProfileCtx.Provider value={value}>{children}</ProfileCtx.Provider>
}

export function useProfile(): ProfileContextValue {
	const ctx = useContext(ProfileCtx)
	if (!ctx) {
		throw new Error('useProfile must be used inside <ProfileProvider>')
	}
	return ctx
}
