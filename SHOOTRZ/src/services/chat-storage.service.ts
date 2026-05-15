import AsyncStorage from '@react-native-async-storage/async-storage'
import type { ChatMessageDto } from '../types/contracts'

/** Single global key from before per-user scoping; migrated on first read. */
const LEGACY_KEY = '@shootrz_chat_conversation_v1'

const PREFIX = '@shootrz_chat_conversation_v1:'

/** AsyncStorage key for a signed-in user; use {@link GUEST_USER_ID} when logged out. */
export const keyForUser = (userId: string) => `${PREFIX}${userId}`

/** Local-only cache when there is no Supabase user (does not share data across accounts). */
export const GUEST_USER_ID = 'anonymous'

export const chatStorageService = {
	async loadConversation(userId: string): Promise<ChatMessageDto[] | null> {
		try {
			const k = keyForUser(userId)
			let raw = await AsyncStorage.getItem(k)
			if (!raw) {
				const legacy = await AsyncStorage.getItem(LEGACY_KEY)
				if (legacy) {
					raw = legacy
					await AsyncStorage.setItem(k, legacy)
					await AsyncStorage.removeItem(LEGACY_KEY)
				}
			}
			if (!raw) return null
			const parsed = JSON.parse(raw)
			if (!Array.isArray(parsed)) return null
			return parsed as ChatMessageDto[]
		} catch {
			return null
		}
	},

	async saveConversation(userId: string, messages: ChatMessageDto[]): Promise<void> {
		try {
			const capped = messages.slice(-200)
			await AsyncStorage.setItem(keyForUser(userId), JSON.stringify(capped))
		} catch (error) {
			console.error('Error saving chat conversation:', error)
		}
	},

	async clearConversation(userId: string): Promise<void> {
		try {
			await AsyncStorage.removeItem(keyForUser(userId))
		} catch {}
	},
}
