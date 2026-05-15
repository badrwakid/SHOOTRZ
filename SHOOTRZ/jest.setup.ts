jest.mock('@expo/vector-icons', () => ({
	Ionicons: (props: Record<string, unknown>) => {
		const React = require('react')
		const { Text } = require('react-native')
		const { name, ...restProps } = props ?? {}

		return React.createElement(Text, { ...restProps }, String(name ?? 'icon'))
	},
}))
