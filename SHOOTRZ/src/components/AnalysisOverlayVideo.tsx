import React from 'react'
import { StyleSheet, ViewStyle } from 'react-native'
import { useEventListener } from 'expo'
import { useVideoPlayer, VideoView } from 'expo-video'

type Props = {
	/** Local file URI (e.g. after downloadAsync) */
	localUri: string
	style: ViewStyle
	/** When enough data is ready to play (replaces expo-av onLoad) */
	onReady: () => void
	onError: () => void
}

/**
 * Annotated MVP overlay playback using expo-video (replaces deprecated expo-av Video).
 */
export function AnalysisOverlayVideo({ localUri, style, onReady, onError }: Props) {
	const player = useVideoPlayer(localUri, p => {
		p.loop = true
	})

	useEventListener(player, 'statusChange', ({ status, error }) => {
		if (status === 'readyToPlay') {
			onReady()
		}
		if (status === 'error' || error) {
			onError()
		}
	})

	return (
		<VideoView
			player={player}
			style={style}
			nativeControls
			contentFit="contain"
		/>
	)
}
