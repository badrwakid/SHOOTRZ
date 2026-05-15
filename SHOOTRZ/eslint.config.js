const { defineConfig } = require('eslint/config')
const expo = require('eslint-config-expo/flat')
const eslintConfigPrettier = require('eslint-config-prettier/flat')
const eslintPluginPrettier = require('eslint-plugin-prettier')

const hexRule = {
	'no-restricted-syntax': [
		'error',
		{
			selector: 'Literal[value=/^#([0-9A-Fa-f]{6})$/]',
			message:
				'Use semantic tokens from src/theme/tokens.ts (or theme helpers), not raw 6-digit hex.',
		},
	],
}

const hexExceptions = {
	'no-restricted-syntax': 'off',
}

module.exports = defineConfig([
	{
		ignores: [
			'**/node_modules/**',
			'**/__graveyard__/**',
			'**/android/**',
			'**/ios/**',
			'**/.expo/**',
			'assets/**',
		],
	},
	...expo,
	{
		plugins: { prettier: eslintPluginPrettier },
		rules: {
			'prettier/prettier': 'warn',
		},
	},
	{ rules: { 'no-console': 'off' } },
	{
		files: ['App.ts', 'App.tsx', 'src/**/*.{ts,tsx}'],
		rules: hexRule,
	},
	{
		files: [
			'src/theme/**/*.ts',
			'src/constants/theme.ts',
			'src/components/buttonTokens.ts',
			'**/__tests__/**',
			'src/components/AppleLogo.tsx',
			'src/components/GoogleLogo.tsx',
			'src/components/CameraRecorder.tsx',
		],
		rules: hexExceptions,
	},
	eslintConfigPrettier,
])
