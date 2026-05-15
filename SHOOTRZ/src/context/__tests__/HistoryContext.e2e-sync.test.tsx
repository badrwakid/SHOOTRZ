import React, { useEffect } from 'react'
import { Text } from 'react-native'
import { act, render, screen, waitFor } from '@testing-library/react-native'
import { useAuth } from '../AuthContext'
import { HistoryProvider, useHistory } from '../HistoryContext'
import { apiService } from '../../services/api.service'

let mockUserId = 'user-e2e-1'

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

describe('HistoryContext E2E sync regression', () => {
	beforeEach(() => {
		mockUserId = 'user-e2e-1'
		;(apiService.getAnalysisHistory as jest.Mock).mockReset()
	})

	test('newly completed analysis appears in progress after refresh/focus', async () => {
		let historyApi: ReturnType<typeof useHistory> | null = null
		const ts = new Date().toISOString()
		;(apiService.getAnalysisHistory as jest.Mock)
			.mockResolvedValueOnce({
				user_id: 'user-e2e-1',
				sessions: [
					{
						session_id: 'older-session-id',
						video_id: 'vid-older',
						timestamp: ts,
						date: ts.slice(0, 10),
						shot_count: 1,
						metrics: [],
					},
				],
				total: 1,
				source: 'analysis_summaries_v1',
			})
			.mockResolvedValueOnce({
				user_id: 'user-e2e-1',
				sessions: [
					{
						session_id: 'latest-session-id',
						video_id: 'vid-latest',
						timestamp: ts,
						date: ts.slice(0, 10),
						shot_count: 1,
						metrics: [{ metric_name: 'knee_flex', value: 0.91 }],
					},
					{
						session_id: 'older-session-id',
						video_id: 'vid-older',
						timestamp: ts,
						date: ts.slice(0, 10),
						shot_count: 1,
						metrics: [],
					},
				],
				total: 2,
				source: 'analysis_summaries_v1',
			})

		const focusListeners: Array<() => void> = []
		const navigation = {
			addListener: jest.fn((event: string, cb: () => void) => {
				if (event === 'focus') {
					focusListeners.push(cb)
				}
				return jest.fn()
			}),
		}

		function ProgressScreenLike(): React.JSX.Element {
			const { user } = useAuth()
			const history = useHistory()
			historyApi = history
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
			return (
				<Text testID="latest-session-id">
					{history.sessions[0]?.session_id ?? 'empty'}
				</Text>
			)
		}

		render(
			<HistoryProvider>
				<ProgressScreenLike />
			</HistoryProvider>,
		)

		await waitFor(() => {
			expect(apiService.getAnalysisHistory).toHaveBeenCalledTimes(1)
		})
		await waitFor(() => {
			expect(screen.getByTestId('latest-session-id').props.children).toBe('older-session-id')
		})

		// Commit flow calls history.refresh(); this bypasses TTL and should pull latest-first.
		await act(async () => {
			const latestFocus = focusListeners[focusListeners.length - 1]
			latestFocus()
			expect(historyApi).not.toBeNull()
			await (historyApi as ReturnType<typeof useHistory>).refresh()
		})

		await waitFor(() => {
			expect(apiService.getAnalysisHistory).toHaveBeenCalledTimes(2)
		})
		await waitFor(() => {
			expect(screen.getByTestId('latest-session-id').props.children).toBe('latest-session-id')
		})
	})
})
