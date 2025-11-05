import { useState, useEffect, useCallback } from 'react'
import { apiService } from '../services/api.service'

interface AnalysisState {
	status: 'idle' | 'uploading' | 'processing' | 'completed' | 'error'
	jobId: string | null
	result: any | null
	error: string | null
	progress: number
}

export function useVideoAnalysis() {
	const [state, setState] = useState<AnalysisState>({
		status: 'idle',
		jobId: null,
		result: null,
		error: null,
		progress: 0,
	})

	const startAnalysis = useCallback(async (videoUri: string) => {
		try {
			setState((prev) => ({ ...prev, status: 'uploading', progress: 0 }))

			const response = await apiService.analyzeVideo(videoUri)
			
			if (response && response.job_id) {
				setState((prev) => ({
					...prev,
					status: 'processing',
					jobId: response.job_id,
					progress: 25,
				}))

				// Poll for results
				pollResults(response.job_id)
			} else {
				throw new Error('Failed to start analysis')
			}
		} catch (error: any) {
			setState((prev) => ({
				...prev,
				status: 'error',
				error: error.message || 'Analysis failed',
			}))
		}
	}, [])

	const pollResults = useCallback(async (jobId: string) => {
		const maxAttempts = 60  // 5 minutes at 5-second intervals
		let attempts = 0

		const poll = async () => {
			try {
				const result = await apiService.getResult(jobId)
				
				if (result) {
					if (result.status === 'completed') {
						setState((prev) => ({
							...prev,
							status: 'completed',
							result: result,
							progress: 100,
						}))
						return
					} else if (result.status === 'failed') {
						setState((prev) => ({
							...prev,
							status: 'error',
							error: result.error || 'Processing failed',
						}))
						return
					}
				}

				// Still processing
				attempts++
				if (attempts < maxAttempts) {
					setState((prev) => ({
						...prev,
						progress: Math.min(25 + (attempts / maxAttempts) * 75, 95),
					}))
					setTimeout(poll, 5000)  // Poll every 5 seconds
				} else {
					setState((prev) => ({
						...prev,
						status: 'error',
						error: 'Analysis timeout - please try again',
					}))
				}
			} catch (error: any) {
				attempts++
				if (attempts < maxAttempts) {
					setTimeout(poll, 5000)
				} else {
					setState((prev) => ({
						...prev,
						status: 'error',
						error: error.message || 'Failed to get results',
					}))
				}
			}
		}

		poll()
	}, [])

	const reset = useCallback(() => {
		setState({
			status: 'idle',
			jobId: null,
			result: null,
			error: null,
			progress: 0,
		})
	}, [])

	return {
		...state,
		startAnalysis,
		reset,
	}
}



