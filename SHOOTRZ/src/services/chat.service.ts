import { API_BASE_URL } from './api.service'
import { supabase } from './supabase.client'
import type {
	ChatRequestDto,
	ChatResponseDto,
	ChatStreamDelta,
	ChatStreamDone,
	ChatHistoryMessage,
	StreamCallbacks,
} from '../types/contracts'

async function getAccessToken(): Promise<string> {
	const { data, error } = await supabase.auth.getSession()
	if (error || !data?.session?.access_token) {
		throw new Error('Not authenticated')
	}
	return data.session.access_token
}

/**
 * Build minimal local context — the server now fetches the bulk of user
 * data from Supabase (analysis_summaries, user_profiles, etc.).  We only
 * send lightweight client hints that have no server-side equivalent yet.
 */
async function buildUserLocalContext() {
	return {}
}

function parseSSEEvents(
	raw: string,
	callbacks: StreamCallbacks,
): void {
	const events = raw.split('\n\n')
	for (const event of events) {
		if (!event.trim()) continue
		const lines = event.split('\n')
		let eventType = ''
		// BUG FIX: Concatenate multiple data: lines per SSE spec (was keeping only last)
		const dataLines: string[] = []
		for (const line of lines) {
			if (line.startsWith('event:')) {
				eventType = line.slice(6).trim()
			} else if (line.startsWith('data:')) {
				dataLines.push(line.slice(5).trim())
			}
		}
		const data = dataLines.join('\n')
		if (!eventType || !data) continue

		try {
			if (eventType === 'delta') {
				const parsed: ChatStreamDelta = JSON.parse(data)
				callbacks.onChunk(parsed.text)
			} else if (eventType === 'done') {
				const parsed: ChatStreamDone = JSON.parse(data)
				callbacks.onDone(parsed)
			} else if (eventType === 'error') {
				const parsed = JSON.parse(data) as { message: string }
				callbacks.onError(new Error(parsed.message))
			}
		} catch {
			/* skip malformed events */
		}
	}
}

export const chatService = {
	/**
	 * Fetch persisted chat history from the backend (Supabase-backed).
	 */
	async getChatHistory(limit: number = 50): Promise<ChatHistoryMessage[]> {
		const token = await getAccessToken()
		const res = await fetch(`${API_BASE_URL}/chat/history?limit=${limit}`, {
			headers: { Authorization: `Bearer ${token}` },
		})
		if (!res.ok) return []
		const data = await res.json()
		return data?.messages ?? []
	},

	/**
	 * Clear all persisted chat history on the server.
	 */
	async clearChatHistory(): Promise<boolean> {
		const token = await getAccessToken()
		const res = await fetch(`${API_BASE_URL}/chat/history`, {
			method: 'DELETE',
			headers: { Authorization: `Bearer ${token}` },
		})
		return res.ok
	},

	/**
	 * Non-streaming (batch) message — kept for backward compatibility.
	 */
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

	/**
	 * Streaming (SSE) message — text chunks arrive progressively via
	 * {@link StreamCallbacks.onChunk}.
	 *
	 * @returns An abort function the caller can invoke to cancel the stream.
	 */
	async sendMessageStream(
		payload: ChatRequestDto,
		callbacks: StreamCallbacks,
	): Promise<() => void> {
		const token = await getAccessToken()
		const userLocalContext = await buildUserLocalContext()

		const body = JSON.stringify({
			messages: payload.messages,
			user_local_context: userLocalContext,
			include_raw_artifacts: payload.includeRawArtifacts ?? false,
			model: payload.model,
		})

		const xhr = new XMLHttpRequest()
		xhr.open('POST', `${API_BASE_URL}/chat/stream`)
		xhr.setRequestHeader('Content-Type', 'application/json')
		xhr.setRequestHeader('Authorization', `Bearer ${token}`)
		xhr.setRequestHeader('Accept', 'text/event-stream')

		let processedLength = 0
		let buffer = ''

		xhr.onreadystatechange = () => {
			if (xhr.readyState >= 3 && xhr.responseText) {
				const newData = xhr.responseText.substring(processedLength)
				processedLength = xhr.responseText.length

				buffer += newData
				const parts = buffer.split('\n\n')
				buffer = parts.pop() || ''

				const completedBlock = parts.join('\n\n')
				if (completedBlock.trim()) {
					parseSSEEvents(completedBlock + '\n\n', callbacks)
				}
			}

			if (xhr.readyState === 4) {
				if (buffer.trim()) {
					parseSSEEvents(buffer, callbacks)
					buffer = ''
				}
				if (xhr.status < 200 || xhr.status >= 300) {
					let detail = `Stream failed: ${xhr.status}`
					try {
						const parsed = JSON.parse(xhr.responseText)
						detail = parsed?.detail || parsed?.message || detail
					} catch {}
					callbacks.onError(new Error(detail))
					// BUG FIX: Always call onDone after error so callers can clean up
					callbacks.onDone({ model: '', context_used: {} })
				}
			}
		}

		xhr.onerror = () => {
			callbacks.onError(new Error('Network error — could not reach Coach J'))
		}

		xhr.send(body)

		return () => {
			try { xhr.abort() } catch {}
		}
	},
}
