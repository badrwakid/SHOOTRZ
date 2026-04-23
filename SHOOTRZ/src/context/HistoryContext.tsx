/**
 * HistoryContext
 * ----------------
 * Single cached source of analysis history for every screen (Home, Progress,
 * Profile, etc). The pre-fix code had ~4 places all calling
 * ``apiService.getAnalysisHistory`` on mount AND on every navigation focus,
 * producing noticeable 5-10s spinners when switching tabs.
 *
 * Behaviour:
 * - First call fetches and caches for ``CACHE_TTL_MS`` (default 30s).
 * - Parallel consumers during an in-flight fetch share the same promise.
 * - ``bump()`` (called after a new analysis completes) invalidates the cache.
 * - ``refresh()`` forces a re-fetch regardless of TTL.
 * - Everything is scoped per ``user.id``; switching users clears the cache.
 */
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
import type { HistoryResponse, HistorySession } from '../types/contracts'

const CACHE_TTL_MS = 30_000

interface HistoryState {
	sessions: HistorySession[]
	loading: boolean
	error: string | null
	/** Monotonically increasing counter; bump to force consumers to re-render. */
	version: number
	/** Returns cached sessions immediately; kicks a refresh only if stale. */
	ensureFresh: () => Promise<HistorySession[]>
	/** Forces a network fetch even if the cache is fresh. */
	refresh: () => Promise<HistorySession[]>
	/** Call after a new analysis completes so consumers pick up the change. */
	bump: () => void
}

const HistoryCtx = createContext<HistoryState | null>(null)

export const HistoryProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
	const { user } = useAuth()
	const [sessions, setSessions] = useState<HistorySession[]>([])
	const [loading, setLoading] = useState(false)
	const [error, setError] = useState<string | null>(null)
	const [version, setVersion] = useState(0)
	const fetchedAtRef = useRef<number>(0)
	const inFlightRef = useRef<Promise<HistorySession[]> | null>(null)
	const lastUserIdRef = useRef<string | null | undefined>(user?.id)

	// Wipe cache on user change.
	useEffect(() => {
		if (lastUserIdRef.current !== user?.id) {
			lastUserIdRef.current = user?.id
			fetchedAtRef.current = 0
			inFlightRef.current = null
			setSessions([])
			setError(null)
			setVersion(v => v + 1)
		}
	}, [user?.id])

	const doFetch = useCallback(async (): Promise<HistorySession[]> => {
		if (!user?.id) {
			setSessions([])
			return []
		}
		if (inFlightRef.current) return inFlightRef.current
		setLoading(true)
		const p = (async () => {
			try {
				const resp: HistoryResponse = await apiService.getAnalysisHistory(100, 0)
				const list = resp?.sessions ?? []
				setSessions(list)
				setError(null)
				fetchedAtRef.current = Date.now()
				setVersion(v => v + 1)
				return list
			} catch (e: any) {
				setError(e?.message || 'Failed to fetch history')
				return []
			} finally {
				setLoading(false)
				inFlightRef.current = null
			}
		})()
		inFlightRef.current = p
		return p
	}, [user?.id])

	const ensureFresh = useCallback(async (): Promise<HistorySession[]> => {
		const age = Date.now() - fetchedAtRef.current
		if (fetchedAtRef.current > 0 && age < CACHE_TTL_MS && !inFlightRef.current) {
			return sessions
		}
		return doFetch()
	}, [sessions, doFetch])

	const refresh = useCallback(async (): Promise<HistorySession[]> => {
		fetchedAtRef.current = 0
		return doFetch()
	}, [doFetch])

	const bump = useCallback(() => {
		fetchedAtRef.current = 0
		// Don't auto-fetch here; consumers will pick this up via their own
		// useFocusEffect/ensureFresh cycle. Avoids a network call even when
		// nobody is mounted.
		setVersion(v => v + 1)
	}, [])

	const value = useMemo<HistoryState>(
		() => ({ sessions, loading, error, version, ensureFresh, refresh, bump }),
		[sessions, loading, error, version, ensureFresh, refresh, bump],
	)

	return <HistoryCtx.Provider value={value}>{children}</HistoryCtx.Provider>
}

export function useHistory(): HistoryState {
	const ctx = useContext(HistoryCtx)
	if (!ctx) {
		throw new Error('useHistory must be used inside <HistoryProvider>')
	}
	return ctx
}
