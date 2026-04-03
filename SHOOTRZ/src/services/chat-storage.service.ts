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
			await AsyncStorage.setItem(KEY, JSON.stringify(messages))
		} catch {}
	},

	async clearConversation(): Promise<void> {
		try {
			await AsyncStorage.removeItem(KEY)
		} catch {}
	},
}




