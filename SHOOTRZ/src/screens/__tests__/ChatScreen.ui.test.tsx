import React from 'react'
import { fireEvent, render } from '@testing-library/react-native'
import { ChatScreen } from '../ChatScreen'

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
	chatStorageService: {
		loadConversation: jest.fn().mockResolvedValue([]),
		saveConversation: jest.fn().mockResolvedValue(undefined),
		clearConversation: jest.fn(),
	},
}))

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
