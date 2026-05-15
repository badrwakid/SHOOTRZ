module.exports = {
	preset: 'jest-expo',
	clearMocks: true,
	testMatch: ['**/__tests__/**/*.[jt]s?(x)'],
	setupFilesAfterEnv: ['<rootDir>/jest.setup.ts'],
}
