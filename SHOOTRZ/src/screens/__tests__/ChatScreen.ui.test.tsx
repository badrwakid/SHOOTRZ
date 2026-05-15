import React from 'react'
import { fireEvent, render, waitFor } from '@testing-library/react-native'
import { ChatScreen } from '../ChatScreen'
import { chatService } from '../../services/chat.service'
import { chatStorageService } from '../../services/chat-storage.service'

let mockUserId: string | null = null

jest.mock('../../context/AuthContext', () => ({
	useAuth: () => ({
		user: mockUserId ? { id: mockUserId } : null,
	}),
}))

jest.mock('../../utils/hapticFeedback', () => ({
	hapticFeedback: {
		warning: jest.fn(),
		medium: jest.fn(),
		success: jest.fn(),
		selection: jest.fn(),
		light: jest.fn(),
	},
}))

jest.mock('../../services/chat.service', () => ({
	chatService: {
		getChatHistory: jest.fn().mockResolvedValue([]),
		sendMessageStream: jest.fn().mockResolvedValue(jest.fn()),
		clearChatHistory: jest.fn().mockResolvedValue(undefined),
	},
}))

jest.mock('../../services/chat-storage.service', () => ({
	GUEST_USER_ID: 'anonymous',
	keyForUser: (id: string) => `@shootrz_chat_conversation_v1:${id}`,
	chatStorageService: {
		loadConversation: jest.fn().mockResolvedValue([]),
		saveConversation: jest.fn().mockResolvedValue(undefined),
		clearConversation: jest.fn(),
	},
}))

beforeEach(() => {
	mockUserId = null
	;(chatStorageService.loadConversation as jest.Mock).mockReset()
	;(chatStorageService.loadConversation as jest.Mock).mockResolvedValue([])
	;(chatStorageService.saveConversation as jest.Mock).mockReset()
	;(chatStorageService.saveConversation as jest.Mock).mockResolvedValue(undefined)
	;(chatStorageService.clearConversation as jest.Mock).mockReset()
	;(chatService.getChatHistory as jest.Mock).mockResolvedValue([])
})

test('chat send button is disabled for empty input', () => {
	const { getByLabelText } = render(<ChatScreen />)
	const sendButton = getByLabelText(/send message/i)
	expect(sendButton.props.accessibilityState.disabled).toBe(true)
})

test('chat send button enables when composer has non-whitespace text', () => {
	const { getByPlaceholderText, getByLabelText } = render(<ChatScreen />)
	fireEvent.changeText(getByPlaceholderText('Ask Coach J...'), 'Hello coach')
	const sendButton = getByLabelText(/send message/i)
	expect(sendButton.props.accessibilityState.disabled).toBe(false)
})

test('chat stream payload excludes empty history messages', async () => {
	(chatService.getChatHistory as jest.Mock).mockResolvedValueOnce([
		{ role: 'assistant', content: '' },
		{ role: 'assistant', content: 'Loaded hint' },
	])

	const { getByPlaceholderText, getByLabelText } = render(<ChatScreen />)

	await waitFor(() => {
		expect(chatService.getChatHistory).toHaveBeenCalledWith(50)
	})

	fireEvent.changeText(getByPlaceholderText('Ask Coach J...'), 'New question')
	fireEvent.press(getByLabelText(/send message/i))

	await waitFor(() => {
		expect(chatService.sendMessageStream).toHaveBeenCalled()
	})

	const [payload] = (chatService.sendMessageStream as jest.Mock).mock.calls[0]
	expect(payload.messages).toEqual([
		{ role: 'assistant', content: 'Loaded hint' },
		{ role: 'user', content: 'New question' },
	])
})

test('does not leak chat cache across users', async () => {
	mockUserId = 'user-a'
	;(chatStorageService.loadConversation as jest.Mock).mockImplementation((userId: string) => {
		if (userId === 'user-a') {
			return Promise.resolve([{ role: 'user' as const, content: 'user-a-msg' }])
		}
		return Promise.resolve([])
	})

	const { rerender, queryByText } = render(<ChatScreen />)
	await waitFor(() => {
		expect(chatStorageService.loadConversation).toHaveBeenCalledWith('user-a')
	})
	await waitFor(() => {
		expect(queryByText('user-a-msg')).not.toBeNull()
	})

	mockUserId = 'user-b'
	rerender(<ChatScreen />)
	await waitFor(() => {
		expect(chatStorageService.loadConversation).toHaveBeenCalledWith('user-b')
	})
	await waitFor(() => {
		expect(queryByText('user-a-msg')).toBeNull()
	})
})
