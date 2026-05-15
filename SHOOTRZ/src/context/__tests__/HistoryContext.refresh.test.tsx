import React, { useEffect } from 'react'
import { Text } from 'react-native'
import { act, render, screen, waitFor } from '@testing-library/react-native'
import { useAuth } from '../AuthContext'
import { HistoryProvider, useHistory } from '../HistoryContext'
import { apiService } from '../../services/api.service'
import { storageService } from '../../services/storage.service'
import { eventBus } from '../../utils/eventBus'
import type { HistorySession } from '../../types/contracts'

let mockUserId = 'user-1'

jest.mock('../AuthContext', () => ({
	useAuth: () => ({
		user: { id: mockUserId },
	}),
}))

jest.mock('../../services/api.service', () => ({
	apiService: {
		getAnalysisHistory: jest.fn(),
	},
}))

jest.mock('../../services/storage.service', () => ({
	storageService: {
		getAnalysisHistory: jest.fn(),
	},
}))

type Deferred<T> = {
	promise: Promise<T>
	resolve: (value: T) => void
	reject: (error: unknown) => void
}

function createDeferred<T>(): Deferred<T> {
	let resolve!: (value: T) => void
	let reject!: (error: unknown) => void
	const promise = new Promise<T>((res, rej) => {
		resolve = res
		reject = rej
	})
	return { promise, resolve, reject }
}

describe('HistoryContext refresh regression', () => {
	beforeEach(() => {
		mockUserId = 'user-1'
		;(apiService.getAnalysisHistory as jest.Mock).mockReset()
		;(storageService.getAnalysisHistory as jest.Mock).mockReset()
	})

	test('refresh starts a new fetch even when an older request is still in flight', async () => {
		let historyApi: ReturnType<typeof useHistory> | null = null

		function Probe(): React.JSX.Element {
			historyApi = useHistory()
			return <></>
		}

		const first = createDeferred<{ sessions: Array<{ id: string }> }>()
		const second = createDeferred<{ sessions: Array<{ id: string }> }>()

		;(apiService.getAnalysisHistory as jest.Mock)
			.mockReturnValueOnce(first.promise)
			.mockReturnValueOnce(second.promise)

		render(
			<HistoryProvider>
				<Probe />
			</HistoryProvider>,
		)

		const getHistory = (): ReturnType<typeof useHistory> => {
			expect(historyApi).not.toBeNull()
			return historyApi as ReturnType<typeof useHistory>
		}

		await act(async () => {
			void getHistory().ensureFresh()
		})

		await waitFor(() => {
			expect(apiService.getAnalysisHistory).toHaveBeenCalledTimes(1)
		})

		let refreshPromise!: Promise<HistorySession[]>
		await act(async () => {
			refreshPromise = getHistory().refresh()
			first.resolve({ sessions: [{ id: 'stale-session' }] })
		})

		expect(apiService.getAnalysisHistory).toHaveBeenCalledTimes(2)

		await act(async () => {
			second.resolve({ sessions: [{ id: 'fresh-session' }] })
			await refreshPromise
		})

		await waitFor(() => {
			expect(getHistory().sessions).toEqual([{ id: 'fresh-session' }])
		})
	})

	test('old user response does not overwrite state after user switch', async () => {
		let historyApi: ReturnType<typeof useHistory> | null = null

		function Probe(): React.JSX.Element {
			historyApi = useHistory()
			return <></>
		}

		const first = createDeferred<{ sessions: Array<{ id: string }> }>()
		const second = createDeferred<{ sessions: Array<{ id: string }> }>()
		;(apiService.getAnalysisHistory as jest.Mock)
			.mockReturnValueOnce(first.promise)
			.mockReturnValueOnce(second.promise)

		const { rerender } = render(
			<HistoryProvider>
				<Probe />
			</HistoryProvider>,
		)

		const getHistory = (): ReturnType<typeof useHistory> => {
			expect(historyApi).not.toBeNull()
			return historyApi as ReturnType<typeof useHistory>
		}

		await act(async () => {
			void getHistory().ensureFresh()
		})
		await waitFor(() => {
			expect(apiService.getAnalysisHistory).toHaveBeenCalledTimes(1)
		})

		mockUserId = 'user-2'
		rerender(
			<HistoryProvider>
				<Probe />
			</HistoryProvider>,
		)

		await act(async () => {
			first.resolve({ sessions: [{ id: 'user1-stale' }] })
		})

		await waitFor(() => {
			expect(getHistory().sessions).toEqual([])
		})

		await act(async () => {
			void getHistory().ensureFresh()
		})
		await waitFor(() => {
			expect(apiService.getAnalysisHistory).toHaveBeenCalledTimes(2)
		})
		await act(async () => {
			second.resolve({ sessions: [{ id: 'user2-fresh' }] })
		})
		await waitFor(() => {
			expect(getHistory().sessions).toEqual([{ id: 'user2-fresh' }])
		})
	})

	test('does not read AsyncStorage for history; server sessions stay authoritative', async () => {
		let historyApi: ReturnType<typeof useHistory> | null = null
		const ts = new Date().toISOString()
		;(apiService.getAnalysisHistory as jest.Mock).mockResolvedValue({
			user_id: 'user-1',
			sessions: [
				{
					session_id: 'server-authoritative',
					video_id: null,
					timestamp: ts,
					date: ts.slice(0, 10),
					shot_count: 1,
					metrics: [],
					/** Would appear in UI if local rows were incorrectly merged. */
					title: 'stale-local-session',
					overall_score: 70,
				},
			],
			total: 1,
		})

		function Probe(): React.JSX.Element {
			const h = useHistory()
			historyApi = h
			return <Text testID="first-session-id">{h.sessions[0]?.session_id ?? 'empty'}</Text>
		}

		const getHistory = (): ReturnType<typeof useHistory> => {
			expect(historyApi).not.toBeNull()
			return historyApi as ReturnType<typeof useHistory>
		}

		render(
			<HistoryProvider>
				<Probe />
			</HistoryProvider>,
		)

		await act(async () => {
			void getHistory().ensureFresh()
		})

		await waitFor(() => {
			expect(apiService.getAnalysisHistory).toHaveBeenCalled()
		})

		await waitFor(() => {
			expect(screen.getByTestId('first-session-id').props.children).toBe('server-authoritative')
		})
		// A mistaken merge of AsyncStorage "local-only" rows could surface this title as a label.
		expect(screen.queryByText('stale-local-session')).toBeNull()
		expect(storageService.getAnalysisHistory).not.toHaveBeenCalled()
	})

	test('revalidates history on screen focus without stale overwrite', async () => {
		const ts = new Date().toISOString()
		const firstResp = {
			user_id: 'user-1',
			sessions: [
				{
					session_id: 'first-focus',
					video_id: null,
					timestamp: ts,
					date: ts.slice(0, 10),
					shot_count: 1,
					metrics: [],
				},
			],
			total: 1,
		}
		const secondResp = {
			user_id: 'user-1',
			sessions: [
				{
					session_id: 'after-focus-refresh',
					video_id: null,
					timestamp: ts,
					date: ts.slice(0, 10),
					shot_count: 1,
					metrics: [],
				},
			],
			total: 1,
		}
		;(apiService.getAnalysisHistory as jest.Mock)
			.mockResolvedValueOnce(firstResp)
			.mockResolvedValueOnce(secondResp)

		const focusListeners: Array<() => void> = []
		const navigation = {
			addListener: jest.fn((event: string, cb: () => void) => {
				if (event === 'focus') {
					focusListeners.push(cb)
				}
				return jest.fn()
			}),
		}

		const baseTime = 1_700_000_000_000
		const dateNow = jest.spyOn(Date, 'now').mockReturnValue(baseTime)

		let historyRef: ReturnType<typeof useHistory> | null = null
		function ProgressScreenLike(): React.JSX.Element {
			const { user } = useAuth()
			const history = useHistory()
			historyRef = history
			useEffect(() => {
				if (!user?.id) return
				history.ensureFresh().catch(() => {})
			}, [user?.id, history])
			useEffect(() => {
				const unsub = navigation.addListener('focus', () => {
					history.ensureFresh().catch(() => {})
				})
				return unsub
			}, [navigation, history])
			return <Text testID="sid">{history.sessions[0]?.session_id ?? 'empty'}</Text>
		}

		render(
			<HistoryProvider>
				<ProgressScreenLike />
			</HistoryProvider>,
		)

		try {
			await waitFor(() => {
				expect(apiService.getAnalysisHistory).toHaveBeenCalledTimes(1)
			})
			await waitFor(() => {
				expect(screen.getByTestId('sid').props.children).toBe('first-focus')
			})

			dateNow.mockReturnValue(baseTime + 31_000)
			const latestFocus = focusListeners[focusListeners.length - 1]
			await act(async () => {
				latestFocus()
			})

			await waitFor(() => {
				expect(apiService.getAnalysisHistory).toHaveBeenCalledTimes(2)
			})
			await waitFor(() => {
				expect(screen.getByTestId('sid').props.children).toBe('after-focus-refresh')
			})
		} finally {
			dateNow.mockRestore()
		}
	})

	test('revalidates when user:updated event is emitted', async () => {
		const ts = new Date().toISOString()
		;(apiService.getAnalysisHistory as jest.Mock)
			.mockResolvedValueOnce({
				user_id: 'user-1',
				sessions: [
					{
						session_id: 'initial-session',
						video_id: null,
						timestamp: ts,
						date: ts.slice(0, 10),
						shot_count: 1,
						metrics: [],
					},
				],
				total: 1,
			})
			.mockResolvedValueOnce({
				user_id: 'user-1',
				sessions: [
					{
						session_id: 'after-user-update',
						video_id: null,
						timestamp: ts,
						date: ts.slice(0, 10),
						shot_count: 1,
						metrics: [],
					},
				],
				total: 1,
			})

		function Probe(): React.JSX.Element {
			const h = useHistory()
			useEffect(() => {
				void h.ensureFresh()
			}, [h])
			return <Text testID="sid">{h.sessions[0]?.session_id ?? 'empty'}</Text>
		}

		render(
			<HistoryProvider>
				<Probe />
			</HistoryProvider>,
		)

		await waitFor(() => {
			expect(apiService.getAnalysisHistory).toHaveBeenCalledTimes(1)
		})
		await waitFor(() => {
			expect(screen.getByTestId('sid').props.children).toBe('initial-session')
		})

		await act(async () => {
			eventBus.emit('user:updated')
		})

		await waitFor(() => {
			expect(apiService.getAnalysisHistory).toHaveBeenCalledTimes(2)
		})
		await waitFor(() => {
			expect(screen.getByTestId('sid').props.children).toBe('after-user-update')
		})
	})
})
