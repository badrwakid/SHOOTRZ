import React from 'react'
import { render, waitFor } from '@testing-library/react-native'
import { HomeScreen } from '../HomeScreen'
import { HistoryProvider } from '../../context/HistoryContext'
import { apiService } from '../../services/api.service'
import { storageService } from '../../services/storage.service'

jest.mock('../../utils/hapticFeedback', () => ({
	hapticFeedback: {
		light: jest.fn(),
		medium: jest.fn(),
		heavy: jest.fn(),
		selection: jest.fn(),
		warning: jest.fn(),
		success: jest.fn(),
	},
}))

jest.mock('../../components/ScoreRing', () => {
	const React = require('react')
	const { View } = require('react-native')
	return {
		ScoreRing: function ScoreRing() {
			return React.createElement(View, { testID: 'score-ring-mock' })
		},
	}
})

jest.mock('../../context/AuthContext', () => ({
	useAuth: () => ({
		user: { id: 'u-auth', name: 'Auth User' },
	}),
}))

jest.mock('../../services/api.service', () => ({
	apiService: {
		getUserStats: jest.fn(),
		getUserStreak: jest.fn(),
		getAnalysisHistory: jest.fn(),
	},
}))

jest.mock('../../services/storage.service', () => ({
	storageService: {
		getAnalysisHistory: jest.fn(),
		getWorkoutHistory: jest.fn(),
		getDrillCompletions: jest.fn(),
	},
}))

test('authenticated home does not use local AsyncStorage analysis history (server is source of truth)', async () => {
	const ts = new Date().toISOString()
	;(apiService.getUserStats as jest.Mock).mockResolvedValue({
		totalSessions: 1,
		avgScore: 70,
		bestScore: 70,
		lastSessionDate: ts,
	})
	;(apiService.getUserStreak as jest.Mock).mockResolvedValue({ currentStreak: 0 })
	;(apiService.getAnalysisHistory as jest.Mock).mockResolvedValue({
		user_id: 'u-auth',
		sessions: [
			{
				session_id: 'from-server',
				video_id: null,
				timestamp: ts,
				date: ts.slice(0, 10),
				shot_count: 1,
				metrics: [],
				overall_score: 70,
			},
		],
		total: 1,
	})
	;(storageService.getAnalysisHistory as jest.Mock).mockResolvedValue([
		{ id: 'stale-local-session', timestamp: ts, scores: { total: 99 } },
	])
	;(storageService.getWorkoutHistory as jest.Mock).mockResolvedValue([])
	;(storageService.getDrillCompletions as jest.Mock).mockResolvedValue([])

	const navigation = { addListener: jest.fn(() => jest.fn()), navigate: jest.fn() }

	render(
		<HistoryProvider>
			<HomeScreen navigation={navigation} />
		</HistoryProvider>,
	)

	await waitFor(() => {
		expect(apiService.getAnalysisHistory).toHaveBeenCalled()
	})
	expect(storageService.getAnalysisHistory).not.toHaveBeenCalled()
})
