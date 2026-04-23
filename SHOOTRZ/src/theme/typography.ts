export const typographyRoleMap = {
	display: {
		fontSize: 38,
		fontWeight: '800',
		fontFamily: 'BarlowCondensedBlack',
		lineHeight: 44,
		letterSpacing: 1,
	},
	headingLg: {
		fontSize: 30,
		fontWeight: '700',
		fontFamily: 'BarlowCondensedBold',
		lineHeight: 36,
		letterSpacing: 0.5,
	},
	headingMd: {
		fontSize: 24,
		fontWeight: '700',
		fontFamily: 'BarlowCondensedBold',
		lineHeight: 30,
		letterSpacing: 0.25,
	},
	headingSm: {
		fontSize: 20,
		fontWeight: '600',
		fontFamily: 'BarlowCondensedBold',
		lineHeight: 26,
	},
	body: {
		fontSize: 15,
		fontWeight: '400',
		fontFamily: 'DMSansRegular',
		lineHeight: 22,
	},
	bodyStrong: {
		fontSize: 15,
		fontWeight: '600',
		fontFamily: 'DMSansSemiBold',
		lineHeight: 22,
	},
	caption: {
		fontSize: 12,
		fontWeight: '400',
		fontFamily: 'DMSansRegular',
		lineHeight: 16,
		letterSpacing: 0.25,
	},
	button: {
		fontSize: 16,
		fontWeight: '700',
		fontFamily: 'DMSansBold',
		lineHeight: 20,
		letterSpacing: 0.5,
		textTransform: 'uppercase',
	},
} as const

export type TypographyRoleMap = typeof typographyRoleMap
