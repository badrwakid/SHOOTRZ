import AsyncStorage from '@react-native-async-storage/async-storage'
import type { ChatMessageDto } from '../types/contracts'

const KEY = '@shootrz_chat_conversation_v1'

export const chatStorageService = {
	async loadConversation(): Promise<ChatMessageDto[] | null> {
		try {
			const raw = await AsyncStorage.getItem(KEY)
			if (!raw) return null
			const parsed = JSON.parse(raw)
			if (!Array.isArray(parsed)) return null
			return parsed as ChatMessageDto[]
		} catch {
			return null
		}
	},

	async saveConversation(messages: ChatMessageDto[]): Promise<void> {
		try {
			// BUG FIX: Cap stored messages to prevent unbounded AsyncStorage growth
			const capped = messages.slice(-200)
			await AsyncStorage.setItem(KEY, JSON.stringify(capped))
		} catch (error) {
			// BUG FIX: Log save errors instead of fully swallowing them
			console.error('Error saving chat conversation:', error)
		}
	},

	async clearConversation(): Promise<void> {
		try {
			await AsyncStorage.removeItem(KEY)
		} catch {}
	},
}




