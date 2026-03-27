import { API_BASE_URL } from './api.service'
import { storageService } from './storage.service'
import { supabase } from './supabase.client'

export type ChatRole = 'user' | 'assistant'

export interface ChatMessageDto {
	role: ChatRole
	content: string
}

export interface ChatRequestDto {
	messages: ChatMessageDto[]
	includeRawArtifacts?: boolean
	model?: string
}

export interface ChatResponseDto {
	assistant_message: string
	context_used: Record<string, any>
	model: string
	usage?: Record<string, any>
}

async function getAccessToken(): Promise<string> {
	const { data, error } = await supabase.auth.getSession()
	if (error || !data?.session?.access_token) {
		throw new Error('Not authenticated')
	}
	return data.session.access_token
}

async function buildUserLocalContext() {
	const [userData, goals, preferences, analysisHistory, drillCompletions] = await Promise.all([
		storageService.getUserData(),
		storageService.getGoals(),
		storageService.getPreferences(),
		storageService.getAnalysisHistory(),
		storageService.getDrillCompletions(),
	])

	// Derive latest_run_id from most recent analysis that has one
	let latestRunId: string | undefined
	if (analysisHistory && analysisHistory.length > 0) {
		for (const analysis of analysisHistory) {
			if (analysis.runId) {
				latestRunId = analysis.runId
				break
			}
		}
	}

	return {
		profile: userData,
		goals,
		preferences,
		analysisHistory,
		drillCompletions,
		latest_run_id: latestRunId,
	}
}

export const chatService = {
	async sendMessage(payload: ChatRequestDto): Promise<ChatResponseDto> {
		const token = await getAccessToken()
		const userLocalContext = await buildUserLocalContext()

		const res = await fetch(`${API_BASE_URL}/chat`, {
			method: 'POST',
			headers: {
				'Content-Type': 'application/json',
				Authorization: `Bearer ${token}`,
			},
			body: JSON.stringify({
				messages: payload.messages,
				user_local_context: userLocalContext,
				include_raw_artifacts: payload.includeRawArtifacts ?? false,
				model: payload.model,
			}),
		})

		if (!res.ok) {
			let detail = `Chat failed: ${res.status}`
			try {
				const data = await res.json()
				detail = data?.detail || data?.message || detail
			} catch {}
			throw new Error(detail)
		}

		return res.json()
	},
}





