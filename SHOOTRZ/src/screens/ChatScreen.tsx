import React, { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import {
	View,
	Text,
	StyleSheet,
	TextInput,
	TouchableOpacity,
	KeyboardAvoidingView,
	Platform,
	FlatList,
	Switch,
	ActivityIndicator,
	ColorValue,
	ScrollView,
} from 'react-native'
import { LinearGradient } from 'expo-linear-gradient'
import { SafeAreaView } from 'react-native-safe-area-context'
import { Ionicons } from '@expo/vector-icons'

import { SHOOTRZ_THEME, COMPONENT_STYLES } from '../constants/theme'
import { hapticFeedback } from '../utils/hapticFeedback'
import { chatService } from '../services/chat.service'
import type { ChatMessageDto } from '../services/chat.service'
import { chatStorageService } from '../services/chat-storage.service'

type MessageStatus = 'sent' | 'sending' | 'failed'

interface UiMessage {
	id: string
	role: 'user' | 'assistant'
	content: string
	createdAt: string
	status: MessageStatus
}

const COACH_GREETING: UiMessage = {
	id: 'coach_greeting',
	role: 'assistant',
	content:
		'I’m Coach J. I can see your SHOOTRZ profile, goals, drills, and recent shot analysis history.\n\nTell me what you want to improve this week (e.g., elbow extension, balance, or release).',
	createdAt: new Date().toISOString(),
	status: 'sent',
}

const QUICK_CHIPS = [
	'Analyze my biggest weakness from recent shots',
	'Give me a 7-day shooting plan',
	'Fix my elbow alignment',
	'Help with balance and footwork',
	'Recommend drills based on my history',
]

function toUiMessages(items: ChatMessageDto[]): UiMessage[] {
	return items.map((m, idx) => ({
		id: `${Date.now()}_${idx}_${m.role}`,
		role: m.role,
		content: m.content,
		createdAt: new Date().toISOString(),
		status: 'sent',
	}))
}

function toPersistedMessages(items: UiMessage[]): ChatMessageDto[] {
	return items
		.filter(m => m.status !== 'failed')
		.filter(m => m.id !== COACH_GREETING.id)
		.map(m => ({ role: m.role, content: m.content }))
}

export const ChatScreen: React.FC = () => {
	const listRef = useRef<FlatList<UiMessage> | null>(null)
	const [messages, setMessages] = useState<UiMessage[]>([COACH_GREETING])
	const [inputText, setInputText] = useState('')
	const [isSending, setIsSending] = useState(false)
	const [errorBanner, setErrorBanner] = useState<string | null>(null)
	const [includeRawArtifacts, setIncludeRawArtifacts] = useState(false)
	const [lastContextUsed, setLastContextUsed] = useState<Record<string, any> | null>(null)

	const contextLabel = useMemo(() => {
		if (!lastContextUsed) return 'Ready'
		const parts: string[] = []
		if (lastContextUsed.profile) parts.push('Profile')
		if (lastContextUsed.has_client_local_context) parts.push('Goals/Drills')
		if (lastContextUsed.recent_videos_count) parts.push('History')
		
		// Show artifacts status if requested
		if (lastContextUsed.artifacts_requested) {
			if (lastContextUsed.artifacts_available) {
				parts.push('Artifacts ✓')
			} else {
				parts.push('Artifacts ✗')
			}
		}
		
		return parts.length ? `Using: ${parts.join(' • ')}` : 'Using context'
	}, [lastContextUsed])

	useEffect(() => {
		let mounted = true
		const load = async () => {
			const saved = await chatStorageService.loadConversation()
			if (!mounted) return
			if (saved && saved.length > 0) {
				const filtered = saved.filter(m => m.content.trim() !== COACH_GREETING.content.trim())
				setMessages([COACH_GREETING, ...toUiMessages(filtered)])
			}
		}
		load()
		return () => {
			mounted = false
		}
	}, [])

	useEffect(() => {
		chatStorageService.saveConversation(toPersistedMessages(messages))
	}, [messages])

	const send = useCallback(async (text: string) => {
		const trimmed = text.trim()
		if (!trimmed || isSending) return

		setErrorBanner(null)
		setIsSending(true)
		hapticFeedback.medium()

		const userMessage: UiMessage = {
			id: `u_${Date.now()}`,
			role: 'user',
			content: trimmed,
			createdAt: new Date().toISOString(),
			status: 'sent',
		}

		setMessages(prev => [...prev, userMessage])
		setInputText('')

		try {
			const outbound = [...messages, userMessage]
				.filter(m => m.status !== 'failed')
				.slice(-20)
				.map(m => ({ role: m.role, content: m.content }))

			const resp = await chatService.sendMessage({
				messages: outbound,
				includeRawArtifacts,
			})

			const assistantMessage: UiMessage = {
				id: `a_${Date.now()}`,
				role: 'assistant',
				content: resp.assistant_message || 'I’m here. Ask me anything about your game.',
				createdAt: new Date().toISOString(),
				status: 'sent',
			}
			setLastContextUsed(resp.context_used || null)
			setMessages(prev => [...prev, assistantMessage])
			hapticFeedback.success()
		} catch (err: any) {
			hapticFeedback.error()
			setErrorBanner(err?.message || 'Failed to reach Coach J. Please try again.')
		} finally {
			setIsSending(false)
		}
	}, [includeRawArtifacts, isSending, messages])

	const handlePressSend = useCallback(() => {
		send(inputText)
	}, [inputText, send])

	const handleClear = useCallback(async () => {
		hapticFeedback.light()
		await chatStorageService.clearConversation()
		setMessages([COACH_GREETING])
		setLastContextUsed(null)
		setErrorBanner(null)
	}, [])

	const renderItem = useCallback(({ item }: { item: UiMessage }) => {
		const isUser = item.role === 'user'
		return (
			<View style={[styles.row, isUser ? styles.rowUser : styles.rowAssistant]}>
				{!isUser && (
					<View style={styles.avatar}>
						<Ionicons name='chatbubbles' size={16} color={SHOOTRZ_THEME.colors.primary} />
					</View>
				)}
				{isUser ? (
					<LinearGradient
						colors={SHOOTRZ_THEME.gradients.primary as [ColorValue, ColorValue]}
						start={{ x: 0, y: 0 }}
						end={{ x: 1, y: 0 }}
						style={styles.bubbleUser}
					>
						<Text style={styles.textUser}>{item.content}</Text>
					</LinearGradient>
				) : (
					<View style={styles.bubbleAssistant}>
						<Text style={styles.coachLabel}>Coach J</Text>
						<Text style={styles.textAssistant}>{item.content}</Text>
					</View>
				)}
			</View>
		)
	}, [])

	return (
		<SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
			<LinearGradient
				colors={[
					SHOOTRZ_THEME.colors.background,
					SHOOTRZ_THEME.colors.surface,
					SHOOTRZ_THEME.colors.background,
				]}
				start={{ x: 0, y: 0 }}
				end={{ x: 1, y: 1 }}
				style={styles.bg}
			>
				<KeyboardAvoidingView
					style={styles.kav}
					behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
				>
					<View style={styles.header}>
						<View style={styles.headerLeft}>
							<View style={styles.headerIcon}>
								<Ionicons name='chatbubbles' size={20} color={SHOOTRZ_THEME.colors.primary} />
							</View>
							<View>
								<Text style={styles.title}>Coach J</Text>
								<Text style={styles.subtitle}>{contextLabel}</Text>
							</View>
						</View>
						<TouchableOpacity onPress={handleClear} style={styles.clearBtn} activeOpacity={0.8}>
							<Ionicons name='trash' size={18} color={SHOOTRZ_THEME.colors.textSecondary} />
						</TouchableOpacity>
					</View>

					{errorBanner ? (
						<View style={styles.errorBanner}>
							<Ionicons name='warning' size={16} color={SHOOTRZ_THEME.colors.error} />
							<Text style={styles.errorText}>{errorBanner}</Text>
						</View>
					) : null}

					<FlatList
						ref={ref => {
							listRef.current = ref
						}}
						style={styles.list}
						contentContainerStyle={styles.listContent}
						data={messages}
						keyExtractor={m => m.id}
						renderItem={renderItem}
						showsVerticalScrollIndicator={false}
						onContentSizeChange={() => listRef.current?.scrollToEnd({ animated: true })}
					/>

					<View style={styles.controls}>
						<View style={styles.toggleRow}>
							<Text style={styles.toggleLabel} numberOfLines={1}>
								Raw artifacts
							</Text>
							<Switch
								value={includeRawArtifacts}
								onValueChange={setIncludeRawArtifacts}
								trackColor={{
									false: SHOOTRZ_THEME.colors.surfaceElevated,
									true: SHOOTRZ_THEME.colors.primary + '55',
								}}
								thumbColor={includeRawArtifacts ? SHOOTRZ_THEME.colors.primary : SHOOTRZ_THEME.colors.textMuted}
							/>
						</View>

						<ScrollView
							horizontal
							showsHorizontalScrollIndicator={false}
							style={styles.chipsScroll}
							contentContainerStyle={styles.chipsContent}
						>
							{QUICK_CHIPS.map(chip => (
								<TouchableOpacity
									key={chip}
									style={styles.chip}
									onPress={() => {
										hapticFeedback.light()
										send(chip)
									}}
									activeOpacity={0.85}
								>
									<Text style={styles.chipText}>{chip}</Text>
								</TouchableOpacity>
							))}
						</ScrollView>

						<View style={styles.inputRow}>
							<TextInput
								style={styles.input}
								value={inputText}
								onChangeText={setInputText}
								placeholder='Ask about your form, drills, or progress…'
								placeholderTextColor={SHOOTRZ_THEME.colors.textMuted}
								multiline
								maxLength={1200}
							/>
							<TouchableOpacity
								onPress={handlePressSend}
								disabled={!inputText.trim() || isSending}
								activeOpacity={0.85}
								style={[styles.sendBtn, (!inputText.trim() || isSending) && styles.sendBtnDisabled]}
							>
								{isSending ? (
									<ActivityIndicator color={SHOOTRZ_THEME.colors.textPrimary} />
								) : (
									<Ionicons name='send' size={18} color={SHOOTRZ_THEME.colors.textPrimary} />
								)}
							</TouchableOpacity>
						</View>
					</View>
				</KeyboardAvoidingView>
			</LinearGradient>
		</SafeAreaView>
	)
}

const styles = StyleSheet.create({
	container: {
		flex: 1,
		backgroundColor: SHOOTRZ_THEME.colors.background,
	},
	bg: {
		flex: 1,
	},
	kav: {
		flex: 1,
	},
	header: {
		paddingHorizontal: SHOOTRZ_THEME.spacing.lg,
		paddingTop: SHOOTRZ_THEME.spacing.lg,
		paddingBottom: SHOOTRZ_THEME.spacing.md,
		flexDirection: 'row',
		alignItems: 'center',
		justifyContent: 'space-between',
		backgroundColor: SHOOTRZ_THEME.colors.surface + 'F0',
		borderBottomWidth: 1,
		borderBottomColor: SHOOTRZ_THEME.colors.surfaceElevated,
	},
	headerLeft: {
		flexDirection: 'row',
		alignItems: 'center',
		gap: SHOOTRZ_THEME.spacing.md,
	},
	headerIcon: {
		width: 36,
		height: 36,
		borderRadius: 18,
		alignItems: 'center',
		justifyContent: 'center',
		backgroundColor: SHOOTRZ_THEME.colors.primary + '22',
	},
	title: {
		...SHOOTRZ_THEME.typography.heading3,
	},
	subtitle: {
		...SHOOTRZ_THEME.typography.bodySmall,
		color: SHOOTRZ_THEME.colors.textSecondary,
		marginTop: 2,
	},
	clearBtn: {
		padding: 10,
		borderRadius: 12,
		backgroundColor: SHOOTRZ_THEME.colors.surfaceElevated + '55',
	},
	errorBanner: {
		marginHorizontal: SHOOTRZ_THEME.spacing.lg,
		marginTop: SHOOTRZ_THEME.spacing.md,
		padding: SHOOTRZ_THEME.spacing.md,
		borderRadius: SHOOTRZ_THEME.borderRadius.lg,
		backgroundColor: SHOOTRZ_THEME.colors.error + '14',
		flexDirection: 'row',
		alignItems: 'center',
		gap: SHOOTRZ_THEME.spacing.sm,
	},
	errorText: {
		flex: 1,
		...SHOOTRZ_THEME.typography.bodySmall,
		color: SHOOTRZ_THEME.colors.error,
	},
	list: {
		flex: 1,
	},
	listContent: {
		paddingHorizontal: SHOOTRZ_THEME.spacing.lg,
		paddingVertical: SHOOTRZ_THEME.spacing.lg,
		gap: SHOOTRZ_THEME.spacing.md,
	},
	row: {
		flexDirection: 'row',
		alignItems: 'flex-end',
	},
	rowUser: {
		justifyContent: 'flex-end',
	},
	rowAssistant: {
		justifyContent: 'flex-start',
	},
	avatar: {
		width: 30,
		height: 30,
		borderRadius: 15,
		alignItems: 'center',
		justifyContent: 'center',
		backgroundColor: SHOOTRZ_THEME.colors.surfaceElevated,
		marginRight: SHOOTRZ_THEME.spacing.sm,
	},
	bubbleUser: {
		maxWidth: '84%',
		paddingHorizontal: SHOOTRZ_THEME.spacing.md,
		paddingVertical: SHOOTRZ_THEME.spacing.sm,
		borderRadius: SHOOTRZ_THEME.borderRadius.xl,
	},
	textUser: {
		...SHOOTRZ_THEME.typography.body,
		color: '#fff',
		lineHeight: 20,
	},
	bubbleAssistant: {
		maxWidth: '84%',
		backgroundColor: SHOOTRZ_THEME.colors.surface,
		borderWidth: 1,
		borderColor: SHOOTRZ_THEME.colors.surfaceElevated,
		paddingHorizontal: SHOOTRZ_THEME.spacing.md,
		paddingVertical: SHOOTRZ_THEME.spacing.sm,
		borderRadius: SHOOTRZ_THEME.borderRadius.xl,
	},
	coachLabel: {
		...SHOOTRZ_THEME.typography.caption,
		color: SHOOTRZ_THEME.colors.primary,
		fontWeight: '700',
		marginBottom: 4,
	},
	textAssistant: {
		...SHOOTRZ_THEME.typography.body,
		color: SHOOTRZ_THEME.colors.textPrimary,
		lineHeight: 20,
	},
	controls: {
		padding: SHOOTRZ_THEME.spacing.lg,
		paddingBottom: SHOOTRZ_THEME.spacing.lg,
		backgroundColor: SHOOTRZ_THEME.colors.surface + 'F8',
		borderTopWidth: 1,
		borderTopColor: SHOOTRZ_THEME.colors.surfaceElevated,
		gap: SHOOTRZ_THEME.spacing.md,
	},
	toggleRow: {
		flexDirection: 'row',
		alignItems: 'center',
		justifyContent: 'space-between',
		minHeight: 32,
	},
	toggleLabel: {
		...SHOOTRZ_THEME.typography.bodySmall,
		color: SHOOTRZ_THEME.colors.textSecondary,
		flexShrink: 1,
		marginRight: SHOOTRZ_THEME.spacing.sm,
	},
	chipsScroll: {
		maxHeight: 36,
	},
	chipsContent: {
		gap: SHOOTRZ_THEME.spacing.sm,
		paddingRight: SHOOTRZ_THEME.spacing.lg,
	},
	chip: {
		paddingHorizontal: SHOOTRZ_THEME.spacing.md,
		paddingVertical: SHOOTRZ_THEME.spacing.sm,
		borderRadius: SHOOTRZ_THEME.borderRadius.xl,
		backgroundColor: SHOOTRZ_THEME.colors.surfaceElevated,
	},
	chipText: {
		...SHOOTRZ_THEME.typography.bodySmall,
		color: SHOOTRZ_THEME.colors.textPrimary,
	},
	inputRow: {
		flexDirection: 'row',
		alignItems: 'flex-end',
		gap: SHOOTRZ_THEME.spacing.md,
	},
	input: {
		flex: 1,
		...COMPONENT_STYLES.input,
		maxHeight: 130,
		textAlignVertical: 'top',
	},
	sendBtn: {
		width: 46,
		height: 46,
		borderRadius: 16,
		alignItems: 'center',
		justifyContent: 'center',
		backgroundColor: SHOOTRZ_THEME.colors.primary,
	},
	sendBtnDisabled: {
		opacity: 0.5,
	},
})
