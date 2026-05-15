import React, { useState, useRef, useEffect, useLayoutEffect, useCallback, useMemo } from 'react'
import {
	View,
	Text,
	StyleSheet,
	TextInput,
	TouchableOpacity,
	FlatList,
	KeyboardAvoidingView,
	Platform,
	Switch,
} from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import { Ionicons } from '@expo/vector-icons'
import { colors, typography, spacing, radius, glass } from '../constants/theme'
import { semanticTokens } from '../theme/tokens'
import { PrimaryButton } from '../components/PrimaryButton'
import { ChatBubble } from '../components/ChatBubble'
import { TypingIndicator } from '../components/TypingIndicator'
import { CoachContextChip } from '../components/CoachContextChip'
import { useAuth } from '../context/AuthContext'
import { chatService } from '../services/chat.service'
import { GUEST_USER_ID, chatStorageService } from '../services/chat-storage.service'
import { hapticFeedback } from '../utils/hapticFeedback'
import type { ChatMessageDto } from '../types/contracts'
import { eventBus } from '../utils/eventBus'

interface UiMessage {
	id: string
	role: 'user' | 'assistant'
	content: string
	status?: 'sending' | 'streaming' | 'sent' | 'error'
}

const COACH_GREETING: UiMessage = {
	id: 'greeting',
	role: 'assistant',
	content: "What's up! I'm Coach J, your AI basketball coach. I can review your shot form, suggest drills, and help you level up. What would you like to work on?",
	status: 'sent',
}

const QUICK_CHIPS = [
	'Review my last shot',
	'Give me a drill plan',
	'Fix my follow-through',
]

function toUiMessages(dtos: ChatMessageDto[]): UiMessage[] {
	return dtos.map((d, i) => ({
		id: `persisted-${i}`,
		role: d.role === 'user' ? 'user' : 'assistant',
		content: d.content,
		status: 'sent' as const,
	}))
}

function toPersistedMessages(msgs: UiMessage[]): ChatMessageDto[] {
	return msgs
		.filter(m => m.id !== 'greeting' && m.status === 'sent')
		.map(m => ({ role: m.role, content: m.content }))
}

export const ChatScreen: React.FC = () => {
	const { user } = useAuth()
	const storageUserId = user?.id ?? GUEST_USER_ID
	const [messages, setMessages] = useState<UiMessage[]>([COACH_GREETING])
	const [inputText, setInputText] = useState('')
	const [isSending, setIsSending] = useState(false)
	const [composerFocused, setComposerFocused] = useState(false)
	const [errorBanner, setErrorBanner] = useState<string | null>(null)
	const [includeRawArtifacts, setIncludeRawArtifacts] = useState(false)
	const [lastContextUsed, setLastContextUsed] = useState<Record<string, any> | null>(null)
	const listRef = useRef<FlatList>(null)
	const abortRef = useRef<(() => void) | null>(null)
	const streamingIdRef = useRef<string | null>(null)
	const prevStorageUserRef = useRef<string | undefined>(undefined)
	const skipSaveOnceRef = useRef(false)
	const currentStorageUserRef = useRef(storageUserId)
	const loadRequestIdRef = useRef(0)
	const userSessionIdRef = useRef(0)

	const loadMessages = useCallback(async () => {
		const requestId = loadRequestIdRef.current + 1
		const requestUserId = storageUserId
		loadRequestIdRef.current = requestId
		const isRequestCurrent = () =>
			currentStorageUserRef.current === requestUserId &&
			loadRequestIdRef.current === requestId

		try {
			const serverMsgs = await chatService.getChatHistory(50)
			if (!isRequestCurrent()) {
				return
			}
			if (serverMsgs && serverMsgs.length > 0) {
				const loaded = toUiMessages(
					serverMsgs.map(m => ({ role: m.role, content: m.content })),
				)
				setMessages([COACH_GREETING, ...loaded])
				return
			}
			const saved = await chatStorageService.loadConversation(requestUserId)
			if (!isRequestCurrent()) {
				return
			}
			if (saved && saved.length > 0) {
				const loaded = toUiMessages(saved)
				setMessages([COACH_GREETING, ...loaded])
			}
		} catch {
			const saved = await chatStorageService.loadConversation(requestUserId)
			if (!isRequestCurrent()) {
				return
			}
			if (saved && saved.length > 0) {
				const loaded = toUiMessages(saved)
				setMessages([COACH_GREETING, ...loaded])
			}
		}
	}, [storageUserId])

	useLayoutEffect(() => {
		currentStorageUserRef.current = storageUserId
		userSessionIdRef.current += 1
		const prev = prevStorageUserRef.current
		if (prev !== undefined && prev !== storageUserId) {
			abortRef.current?.()
			abortRef.current = null
			streamingIdRef.current = null
			skipSaveOnceRef.current = true
		}
		prevStorageUserRef.current = storageUserId
		setMessages([COACH_GREETING])
		setLastContextUsed(null)
		setIsSending(false)
	}, [storageUserId])

	useEffect(() => {
		loadMessages()
		return () => {
			abortRef.current?.()
		}
	}, [loadMessages])

	useEffect(() => {
		const unsubscribe = eventBus.on('user:updated', () => {
			setLastContextUsed(null)
			loadMessages()
		})
		return unsubscribe
	}, [loadMessages])

	useEffect(() => {
		if (!streamingIdRef.current) {
			if (skipSaveOnceRef.current) {
				skipSaveOnceRef.current = false
				return
			}
			chatStorageService
				.saveConversation(storageUserId, toPersistedMessages(messages))
				.catch(() => {})
		}
	}, [messages, storageUserId])

	const contextLabel = useMemo(() => {
		if (!lastContextUsed) return null
		const parts: string[] = []
		if (lastContextUsed.profile) parts.push('Profile')
		if (lastContextUsed.goals_and_drills) parts.push('Goals')
		if (lastContextUsed.history) parts.push('History')
		return parts.length > 0 ? parts.join(' + ') : null
	}, [lastContextUsed])

	const send = useCallback(
		(text: string) => {
			const trimmed = text.trim()
			if (!trimmed || isSending) return
			setInputText('')
			setErrorBanner(null)
			hapticFeedback.medium()

			const userId = `user-${Date.now()}`
			const assistantId = `assistant-${Date.now()}`
			const requestUserId = storageUserId
			const sessionId = userSessionIdRef.current
			const isCurrentSession = () =>
				currentStorageUserRef.current === requestUserId &&
				userSessionIdRef.current === sessionId
			streamingIdRef.current = assistantId

			setMessages(prev => [
				...prev,
				{ id: userId, role: 'user', content: trimmed, status: 'sent' },
				{ id: assistantId, role: 'assistant', content: '', status: 'sending' },
			])
			setIsSending(true)

			const outbound = [
				...messages
					.filter(m => m.id !== 'greeting' && m.status === 'sent')
					.filter(m => m.content.trim().length > 0)
					.slice(-20)
					.map(m => ({ role: m.role, content: m.content })),
				{ role: 'user' as const, content: trimmed },
			]

			chatService.sendMessageStream(
				{ messages: outbound, includeRawArtifacts },
				{
					onChunk: (chunk: string) => {
						if (!isCurrentSession()) {
							return
						}
						setMessages(prev =>
							prev.map(m =>
								m.id === assistantId ? { ...m, content: m.content + chunk, status: 'streaming' } : m,
							),
						)
					},
					onDone: (metadata?: any) => {
						if (!isCurrentSession()) {
							return
						}
						streamingIdRef.current = null
						setMessages(prev =>
							prev.map(m =>
								m.id === assistantId ? { ...m, status: 'sent' } : m,
							),
						)
						if (metadata?.context_used) setLastContextUsed(metadata.context_used)
						setIsSending(false)
						hapticFeedback.success()
					},
					onError: (err: Error) => {
						if (!isCurrentSession()) {
							return
						}
						streamingIdRef.current = null
						setMessages(prev => prev.filter(m => m.id !== assistantId))
						setErrorBanner(err.message || 'Something went wrong')
						setIsSending(false)
						hapticFeedback.warning()
					},
				},
			)
				.then(abort => {
					if (!isCurrentSession()) {
						abort()
						return
					}
					abortRef.current = abort
				})
				.catch((err: Error) => {
					if (!isCurrentSession()) {
						return
					}
					streamingIdRef.current = null
					setMessages(prev => prev.filter(m => m.id !== assistantId))
					setErrorBanner(err.message || 'Something went wrong')
					setIsSending(false)
					hapticFeedback.warning()
				})
		},
		[isSending, messages, includeRawArtifacts, storageUserId],
	)

	const handleClear = useCallback(() => {
		abortRef.current?.()
		chatStorageService.clearConversation(storageUserId)
		chatService.clearChatHistory().catch(() => {})
		setMessages([COACH_GREETING])
		setLastContextUsed(null)
		setErrorBanner(null)
		setIsSending(false)
		hapticFeedback.light()
	}, [storageUserId])

	const renderItem = useCallback(
		({ item }: { item: UiMessage }) => {
			if (item.status === 'sending') return <TypingIndicator />
			return (
				<ChatBubble
					message={item.content}
					role={item.role === 'user' ? 'user' : 'coach'}
					streaming={item.status === 'streaming'}
				/>
			)
		},
		[],
	)

	const hasMessages = messages.length > 1

	return (
		<SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
			<KeyboardAvoidingView
				style={styles.flex}
				behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
				keyboardVerticalOffset={0}
			>
				{/* Header */}
				<View style={styles.header}>
					<View style={styles.coachAvatar}>
						<Text style={styles.avatarText}>J</Text>
					</View>
					<View style={styles.headerInfo}>
						<Text style={styles.headerTitle}>Coach J</Text>
						<Text style={styles.headerSub}>AI Basketball Coach</Text>
					</View>
					<TouchableOpacity onPress={handleClear} hitSlop={{ top: 8, bottom: 8, left: 8, right: 8 }}>
						<Ionicons name="refresh-outline" size={20} color={colors.text.tertiary} />
					</TouchableOpacity>
				</View>

				{contextLabel ? (
					<View style={styles.chipWrap}>
						<CoachContextChip sessionLabel={contextLabel} onDismiss={() => setLastContextUsed(null)} />
					</View>
				) : null}

				{errorBanner ? (
					<View style={styles.errorBanner}>
						<Ionicons name="alert-circle" size={14} color={colors.error} />
						<Text style={styles.errorBannerText}>{errorBanner}</Text>
					</View>
				) : null}

				{/* Messages */}
				<FlatList
					ref={listRef}
					data={messages}
					renderItem={renderItem}
					keyExtractor={item => item.id}
					contentContainerStyle={styles.listContent}
					showsVerticalScrollIndicator={false}
					keyboardShouldPersistTaps="handled"
					onContentSizeChange={() => listRef.current?.scrollToEnd({ animated: true })}
					onLayout={() => listRef.current?.scrollToEnd({ animated: false })}
				/>

				{/* Quick Chips */}
				{!hasMessages ? (
					<View style={styles.chipsRow}>
						{QUICK_CHIPS.map(chip => (
							<TouchableOpacity
								key={chip}
								style={styles.chip}
								onPress={() => { hapticFeedback.selection(); send(chip) }}
							>
								<Text style={styles.chipText}>{chip}</Text>
							</TouchableOpacity>
						))}
					</View>
				) : null}

				{/* Artifacts toggle */}
				<View style={styles.toggleRow}>
					<Text style={styles.toggleLabel}>Include raw artifacts</Text>
					<Switch
						value={includeRawArtifacts}
						onValueChange={v => { hapticFeedback.selection(); setIncludeRawArtifacts(v) }}
						trackColor={{ false: colors.bg.elevated, true: colors.brand.cyanDim }}
						thumbColor={includeRawArtifacts ? colors.brand.cyan : colors.text.tertiary}
					/>
				</View>

				{/* Input */}
				<View style={styles.inputRow}>
					<TextInput
						style={[
							styles.input,
							composerFocused ? styles.inputFocus : null,
						]}
						placeholder="Ask Coach J..."
						placeholderTextColor={colors.text.tertiary}
						value={inputText}
						onChangeText={setInputText}
						multiline
						maxLength={1000}
						editable={!isSending}
						onFocus={() => setComposerFocused(true)}
						onBlur={() => setComposerFocused(false)}
					/>
					<PrimaryButton
						label="Send"
						a11yLabel={isSending ? 'Sending' : 'Send message'}
						icon={isSending ? undefined : 'send'}
						iconOnly
						size="md"
						variant="orange"
						loading={isSending}
						disabled={!inputText.trim() || isSending}
						onPress={() => send(inputText)}
					/>
				</View>
			</KeyboardAvoidingView>
		</SafeAreaView>
	)
}

const styles = StyleSheet.create({
	container: {
		flex: 1,
		backgroundColor: colors.bg.primary,
	},
	flex: { flex: 1 },
	header: {
		flexDirection: 'row',
		alignItems: 'center',
		gap: spacing[3],
		paddingHorizontal: spacing.screenPadding,
		paddingVertical: spacing[3],
		borderBottomWidth: 1,
		borderBottomColor: colors.border.subtle,
	},
	coachAvatar: {
		width: 36,
		height: 36,
		borderRadius: 18,
		backgroundColor: colors.brand.cyan,
		alignItems: 'center',
		justifyContent: 'center',
	},
	avatarText: {
		fontSize: typography.size.sm,
		fontWeight: typography.weight.bold,
		color: colors.bg.primary,
	},
	headerInfo: { flex: 1 },
	headerTitle: {
		fontSize: typography.size.base,
		fontWeight: typography.weight.semibold,
		color: colors.text.primary,
	},
	headerSub: {
		fontSize: typography.size.xs,
		color: colors.brand.cyan,
	},
	chipWrap: {
		paddingHorizontal: spacing.screenPadding,
		paddingTop: spacing[2],
	},
	errorBanner: {
		flexDirection: 'row',
		alignItems: 'center',
		gap: spacing[2],
		backgroundColor: colors.error + '20',
		paddingHorizontal: spacing.screenPadding,
		paddingVertical: spacing[2],
	},
	errorBannerText: {
		fontSize: typography.size.xs,
		color: colors.error,
		flex: 1,
	},
	listContent: {
		paddingHorizontal: spacing.screenPadding,
		paddingVertical: spacing[3],
	},
	chipsRow: {
		flexDirection: 'row',
		flexWrap: 'wrap',
		gap: spacing[2],
		paddingHorizontal: spacing.screenPadding,
		paddingBottom: spacing[3],
	},
	chip: {
		backgroundColor: glass.cyan.bg,
		borderWidth: 1,
		borderColor: glass.cyan.border,
		borderRadius: radius.pill,
		paddingHorizontal: spacing[3],
		paddingVertical: spacing[2],
	},
	chipText: {
		fontSize: typography.size.sm,
		color: colors.brand.cyan,
	},
	toggleRow: {
		flexDirection: 'row',
		alignItems: 'center',
		justifyContent: 'space-between',
		paddingHorizontal: spacing.screenPadding,
		paddingVertical: spacing[1],
	},
	toggleLabel: {
		fontSize: typography.size.xs,
		color: colors.text.tertiary,
	},
	inputRow: {
		flexDirection: 'row',
		alignItems: 'flex-end',
		gap: spacing[2],
		paddingHorizontal: spacing.screenPadding,
		paddingVertical: spacing[3],
		borderTopWidth: 1,
		borderTopColor: colors.border.subtle,
	},
	input: {
		flex: 1,
		backgroundColor: colors.bg.secondary,
		borderRadius: radius['2xl'],
		borderWidth: 1,
		borderColor: 'transparent',
		paddingHorizontal: spacing[4],
		paddingVertical: spacing[3],
		fontSize: typography.size.base,
		color: colors.text.primary,
		maxHeight: 100,
	},
	inputFocus: {
		borderColor: semanticTokens.focus.ring,
	},
})
