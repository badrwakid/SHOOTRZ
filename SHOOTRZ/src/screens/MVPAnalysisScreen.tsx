import React, { useState, useRef, useMemo, useEffect } from 'react'
import {
	View,
	Text,
	StyleSheet,
	ScrollView,
	TouchableOpacity,
	Alert,
	ActivityIndicator,
	Animated,
} from 'react-native'
import { AnalysisOverlayVideo } from '../components/AnalysisOverlayVideo'
import { SafeAreaView } from 'react-native-safe-area-context'
import * as ImagePicker from 'expo-image-picker'
import * as FileSystem from 'expo-file-system/legacy'
import { Ionicons } from '@expo/vector-icons'
import { useAuth } from '../context/AuthContext'
import { useHistory } from '../context/HistoryContext'
import { storageService } from '../services/storage.service'
import { CameraRecorder } from '../components/CameraRecorder'
import { ScoreRing } from '../components/ScoreRing'
import { TierBadge } from '../components/TierBadge'
import { MetricCard } from '../components/MetricCard'
import { SectionHeader } from '../components/SectionHeader'
import { PrimaryButton } from '../components/PrimaryButton'
import { AngleGraph } from '../components/AngleGraph'
import { API_BASE_URL, apiService } from '../services/api.service'
import { colors, typography, spacing, radius, animation, getScoreTier } from '../constants/theme'
import { semanticTokens } from '../theme/tokens'
import { hapticFeedback } from '../utils/hapticFeedback'
import { useNavigation } from '@react-navigation/native'
import type { MVPMetric, MVPResultResponse, MVPResultStatus } from '../types/contracts'

interface AnalysisResult extends MVPResultResponse {
	contract_version?: string
	run_id: string
	status: MVPResultStatus
	overall_score: number
	feedback_summary: string
	feedback_bullets?: string[]
	metrics: MVPMetric[]
	score_components?: Array<{ name: string; value: number | null; weight: number; unit?: string; explanation?: string }>
	shot_window: { start_frame?: number; crouch_frame?: number; release_frame?: number; end_frame?: number; confidence?: string; confidence_score?: number }
	events?: Record<string, any>
	angles_data: { frames: number[]; timestamps: number[]; elbow: Array<number | null>; knee: Array<number | null>; wrist: Array<number | null> }
	artifacts: { overlay_video?: string | null; angles_csv?: string; report_json?: string; event_candidates?: string; warnings?: string }
	key_frame_images?: Record<string, string>
	diagnostics?: Record<string, unknown>
	quality_warnings?: string[]
}

const PROCESSING_LABELS = [
	'Analyzing pose...',
	'Detecting shot phases...',
	'Computing metrics...',
	'Generating feedback...',
]

export const MVPAnalysisScreen: React.FC = () => {
	const navigation = useNavigation()
	const { user } = useAuth()
	const history = useHistory()
	const [isAnalyzing, setIsAnalyzing] = useState(false)
	const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null)
	const [showCameraRecorder, setShowCameraRecorder] = useState(false)
	const [shootingSide, setShootingSide] = useState<'auto' | 'left' | 'right'>('auto')
	const lastRequestRef = useRef<string | null>(null)
	const overlayUri = useMemo(() => {
		if (!analysisResult?.artifacts?.overlay_video) return null
		return `${API_BASE_URL}${analysisResult.artifacts.overlay_video}`
	}, [analysisResult?.artifacts?.overlay_video])
	const [isOverlayLoading, setIsOverlayLoading] = useState(false)
	const [overlayError, setOverlayError] = useState<string | null>(null)
	const [overlayLocalUri, setOverlayLocalUri] = useState<string | null>(null)
	const [overlayKey, setOverlayKey] = useState(0)
	const [processingLabel, setProcessingLabel] = useState(0)
	const processingPulse = useRef(new Animated.Value(0.4)).current

	useEffect(() => {
		if (!isAnalyzing) return
		const interval = setInterval(() => setProcessingLabel(p => (p + 1) % PROCESSING_LABELS.length), 2000)
		const anim = Animated.loop(
			Animated.sequence([
				Animated.timing(processingPulse, { toValue: 1, duration: 800, useNativeDriver: true }),
				Animated.timing(processingPulse, { toValue: 0.4, duration: 800, useNativeDriver: true }),
			]),
		)
		anim.start()
		return () => { clearInterval(interval); anim.stop() }
	}, [isAnalyzing])

	const downloadOverlayToLocal = async (): Promise<string | null> => {
		if (!overlayUri || !analysisResult?.run_id) { setOverlayError('No overlay URL.'); return null }
		try {
			setIsOverlayLoading(true)
			const cacheDir = (FileSystem as any).cacheDirectory ?? (FileSystem as any).documentDirectory ?? ''
			const targetPath = `${cacheDir}overlay_${analysisResult.run_id}.mp4`
			const res = await FileSystem.downloadAsync(overlayUri, targetPath)
			setOverlayLocalUri(res.uri); setOverlayError(null)
			return res.uri
		} catch { setOverlayError('Unable to load overlay.'); return null }
		finally { setIsOverlayLoading(false) }
	}

	useEffect(() => {
		let canceled = false
		const loadOverlay = async () => {
			if (!overlayUri) return
			setOverlayError(null); setIsOverlayLoading(true); setOverlayLocalUri(null)
			setOverlayKey(p => p + 1)
			const localUri = await downloadOverlayToLocal()
			if (canceled) return
			if (localUri) { setOverlayLocalUri(localUri); setOverlayError(null) }
			else { setOverlayError('Could not load overlay.') }
			setIsOverlayLoading(false)
		}
		loadOverlay()
		return () => { canceled = true }
	}, [overlayUri])

	const pickVideo = async () => {
		const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync()
		if (status !== 'granted') { Alert.alert('Permission Required', 'Camera roll access is needed.'); return }
		const result = await ImagePicker.launchImageLibraryAsync({ mediaTypes: 'videos', allowsEditing: false, quality: 1, videoMaxDuration: 30 })
		if (!result.canceled && result.assets[0]) await handleAnalyzeVideo(result.assets[0].uri)
	}

	const recordVideo = () => { setShowCameraRecorder(true); hapticFeedback.medium() }
	const handleVideoRecorded = async (uri: string) => { setShowCameraRecorder(false); await handleAnalyzeVideo(uri) }
	const handleCameraCancel = () => setShowCameraRecorder(false)

	const handleAnalyzeVideo = async (videoUri: string) => {
		if (isAnalyzing || lastRequestRef.current === videoUri) return
		lastRequestRef.current = videoUri
		setIsAnalyzing(true); setAnalysisResult(null); setOverlayError(null); setIsOverlayLoading(true); setOverlayLocalUri(null)

		try {
			const uploadResponse = await apiService.analyzeMVP(videoUri, shootingSide)
			if (uploadResponse.job_id) {
				// Exponential-ish poll: most real analyses finish in 2-5s on warm
				// ProcessPool workers. The previous flat 1000ms wasted ~700ms of
				// wall time per analysis and had a 120s hard cap.
				const POLL_SCHEDULE_MS = [300, 400, 600, 800, 1000]
				const POLL_CEILING_MS = 1500
				const MAX_WALL_TIME_MS = 90_000
				const start = Date.now()
				let pollIdx = 0
				while (Date.now() - start < MAX_WALL_TIME_MS) {
					const waitMs = POLL_SCHEDULE_MS[Math.min(pollIdx, POLL_SCHEDULE_MS.length - 1)] ?? POLL_CEILING_MS
					await new Promise(r => setTimeout(r, waitMs))
					pollIdx += 1
					const res = await apiService.getMVPResult(uploadResponse.job_id)
					if (res.status === 'completed' || res.status === 'completed_low_quality') {
						const v: AnalysisResult = {
							...res, run_id: res.run_id ?? '', status: res.status,
							overall_score: res.overall_score ?? 0,
							feedback_summary:
								res.status === 'completed_low_quality'
									? (res.feedback_summary || 'We could not analyse this clip. Try again with better lighting and a full-body side angle.')
									: (res.feedback_summary || 'Analysis completed'),
							feedback_bullets: Array.isArray(res.feedback_bullets) ? res.feedback_bullets : [],
							metrics: Array.isArray(res.metrics) ? res.metrics : [],
							score_components: Array.isArray(res.score_components) ? res.score_components : [],
							shot_window: res.shot_window || {}, events: res.events || {},
							angles_data: res.angles_data || { frames: [], timestamps: [], elbow: [], knee: [], wrist: [] },
							artifacts: res.artifacts || {}, key_frame_images: res.key_frame_images || {},
							diagnostics: res.diagnostics || {},
						}
						setAnalysisResult(v); hapticFeedback.success()
						setOverlayError(null); setIsOverlayLoading(true)
						const jobId = uploadResponse.job_id
						if (user?.id && jobId) {
							try {
								await apiService.completeMVPAnalysis(jobId)
							} catch (e) {
								console.warn('completeMVPAnalysis failed, retrying once', e)
								try {
									await apiService.completeMVPAnalysis(jobId)
								} catch (e2) {
									console.warn('completeMVPAnalysis failed after retry', e2)
								}
							}
							// Invalidate shared history cache so Home/Progress pick
							// this session up next time they mount or focus.
							history.bump()
						}
						try {
							const fmv = (k: string) => { const m = v.metrics.find(m2 => m2.name?.toLowerCase().includes(k)); return Number.isFinite(m?.value) ? (m?.value as number) : 0 }
							const fcv = (k: string) => { const c = v.score_components?.find(c2 => c2.name?.toLowerCase().includes(k)); return Number.isFinite(c?.value) ? (c?.value as number) : 0 }
							storageService.saveAnalysisResult({
								id: `${Date.now()}`, userId: user?.id || 'local', timestamp: new Date().toISOString(),
								runId: v.run_id || undefined,
								scores: { elbow: fmv('elbow'), balance: fcv('balance'), release: fcv('release'), alignment: fcv('loading'), total: v.overall_score ?? 0 },
								feedback: v.feedback_bullets?.length ? v.feedback_bullets : v.feedback_summary ? [v.feedback_summary] : [],
								angles: { elbow: fmv('elbow'), knee: fmv('knee'), release: fmv('wrist'), bodyAlignment: fcv('balance') },
								mvp: { scoreComponents: v.score_components?.map(c => ({ name: c.name, value: c.value, weight: c.weight })), keyFrameImages: v.key_frame_images, shotWindow: v.shot_window, events: v.events, diagnostics: v.diagnostics },
							} as any, user?.id).catch(() => {})
						} catch {}
						return
					}
					if (res.status === 'failed') throw new Error(res.error || res.error_detail || 'Analysis failed')
				}
				throw new Error('Analysis timed out.')
			} else { throw new Error('Failed to start analysis') }
		} catch (error: any) {
			hapticFeedback.error(); setIsOverlayLoading(false)
			let msg = error.message || 'Failed to analyze video.'
			if (msg.includes('timeout')) msg = 'Analysis took too long. Try a shorter video (3-10s).'
			else if (msg.includes('Network') || msg.includes('Could not reach')) msg = 'Cannot connect to server.'
			else if (msg.includes('pose')) msg = 'Could not detect your form. Ensure visibility and lighting.'
			Alert.alert('Analysis Failed', msg)
		} finally {
			setIsAnalyzing(false)
			setTimeout(() => { lastRequestRef.current = null }, 5000)
		}
	}

	const formatFrameValue = (v?: number) => Number.isFinite(v) ? v : '--'

	if (showCameraRecorder) {
		return <CameraRecorder onVideoRecorded={handleVideoRecorded} onCancel={handleCameraCancel} maxDuration={30} />
	}

	return (
		<SafeAreaView style={styles.container} edges={['top', 'left', 'right']}>
			<ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.scrollContent}>
				{!analysisResult && !isAnalyzing ? (
					<View style={styles.uploadSection}>
						<View style={styles.uploadZone}>
							<Ionicons name="basketball-outline" size={56} color={colors.brand.chrome} />
							<Text style={styles.uploadTitle}>Upload or Record Your Shot</Text>
							<Text style={styles.uploadHint}>MP4, MOV - Max 100MB</Text>

							<View style={styles.sideSelector}>
								<Text style={styles.sideSelectorLabel}>Shooting Side</Text>
								<View style={styles.sidePills}>
									{(['auto', 'left', 'right'] as const).map(side => (
										<TouchableOpacity
											key={side}
											style={[styles.sidePill, shootingSide === side && styles.sidePillActive]}
											onPress={() => { hapticFeedback.selection(); setShootingSide(side) }}
											activeOpacity={0.8}
										>
											<Text style={[styles.sidePillText, shootingSide === side && styles.sidePillTextActive]}>
												{side === 'auto' ? 'Auto' : side.charAt(0).toUpperCase() + side.slice(1)}
											</Text>
										</TouchableOpacity>
									))}
								</View>
							</View>

							<View style={styles.uploadButtons}>
								<PrimaryButton label="Record Video" icon="videocam" onPress={recordVideo} size="lg" fullWidth />
								<PrimaryButton label="Upload Video" icon="cloud-upload" onPress={pickVideo} size="lg" fullWidth variant="cyan" />
							</View>
						</View>
					</View>
				) : isAnalyzing ? (
					<View style={styles.processingSection}>
						<Animated.View style={[styles.processingRing, { opacity: processingPulse }]}>
							<View style={styles.processingRingInner} />
						</Animated.View>
						<Text style={styles.processingLabel}>{PROCESSING_LABELS[processingLabel]}</Text>
						<Text style={styles.processingHint}>This usually takes 15-30 seconds</Text>
					</View>
				) : analysisResult ? (
					<View>
						{analysisResult.status === 'completed_low_quality' ? (
							<View style={styles.lowQualityBanner}>
								<Ionicons name="warning" size={22} color={colors.warning} />
								<View style={{ flex: 1 }}>
									<Text style={styles.lowQualityTitle}>We could not analyse this clip</Text>
									<Text style={styles.lowQualityText}>
										{analysisResult.feedback_summary || 'Try again with a full-body side view and better lighting.'}
									</Text>
									{analysisResult.quality_warnings?.length ? (
										<Text style={styles.lowQualityHint}>
											Reason: {analysisResult.quality_warnings.join(', ')}
										</Text>
									) : null}
								</View>
							</View>
						) : (
							<View style={styles.scoreHero}>
								<Text style={styles.scoreHeroLabel}>YOUR SHOT SCORE</Text>
								<ScoreRing score={analysisResult.overall_score} size="hero" animated />
								<TierBadge tier={getScoreTier(analysisResult.overall_score)} size="md" />
								<Text style={styles.scoreHeroDate}>{new Date().toLocaleDateString()}</Text>
							</View>
						)}

						{/* Tracking quality chip — drives user expectations for why a
						     metric might be N/A. Values come from the backend's
						     pose_overall_confidence (mean landmark visibility). */}
						{typeof analysisResult.pose_overall_confidence === 'number' ? (
							(() => {
								const q = Math.round((analysisResult.pose_overall_confidence || 0) * 100)
								const tone =
									q >= 75 ? colors.success : q >= 55 ? colors.warning : colors.error
								const label =
									q >= 75 ? 'Great tracking' : q >= 55 ? 'OK tracking' : 'Weak tracking'
								return (
									<View style={[styles.trackingChip, { borderColor: tone }]}>
										<Ionicons name="body" size={16} color={tone} />
										<Text style={[styles.trackingChipText, { color: tone }]}>
											{label} · {q}%
										</Text>
										{q < 55 ? (
											<Text style={styles.trackingChipHint}>
												Re-record side-on with full body in frame.
											</Text>
										) : null}
									</View>
								)
							})()
						) : null}

						{/* Metric Breakdown */}
						{analysisResult.metrics && analysisResult.metrics.length > 0 ? (
							<View style={styles.section}>
								<SectionHeader title="Biomechanics" />
								<View style={styles.metricsGrid}>
									{analysisResult.metrics.map((m, i) => {
										const isLowConf = m.verdict === 'Low Confidence'
										const rawLabel = m.name ? m.name.replace(/_/g, ' ') : 'Metric'
										const displayValue = isLowConf
											? '--'
											: (m.value != null ? m.value.toFixed(1) : '--')
										const displayUnit = isLowConf ? 'N/A' : (m.unit || '')
										return (
											<View key={i} style={styles.metricItem}>
												<MetricCard
													label={rawLabel}
													value={displayValue}
													unit={displayUnit}
													score={
														!isLowConf && m.confidence != null
															? Math.round(m.confidence * 100)
															: undefined
													}
													description={m.explanation}
												/>
											</View>
										)
									})}
								</View>
							</View>
						) : null}

						{/* Phase Timeline */}
						{analysisResult.shot_window?.start_frame != null ? (
							<View style={styles.section}>
								<SectionHeader title="Shot Phases" />
								<View style={styles.phaseBar}>
									{['Setup', 'Load', 'Release', 'Follow-Through'].map((phase, i) => (
										<View key={phase} style={[styles.phaseBlock, { backgroundColor: [colors.brand.orangeDim, colors.brand.cyanDim, colors.brand.orangeGlow, colors.brand.chromeDim][i] }]}>
											<Text style={styles.phaseText}>{phase}</Text>
										</View>
									))}
								</View>
								<Text style={styles.phaseInfo}>
									Shot Window: Frame {formatFrameValue(analysisResult.shot_window.start_frame)} - {formatFrameValue(analysisResult.shot_window.end_frame)}
								</Text>
							</View>
						) : null}

						{/* AI Feedback */}
						{analysisResult.feedback_bullets && analysisResult.feedback_bullets.length > 0 ? (
							<View style={styles.section}>
								<SectionHeader title="Feedback" />
								{analysisResult.feedback_bullets.map((fb, i) => (
									<View key={i} style={styles.feedbackCard}>
										<Ionicons
											name={i < 2 ? 'checkmark-circle' : 'information-circle'}
											size={18}
											color={i < 2 ? colors.success : colors.warning}
										/>
										<Text style={styles.feedbackText}>{fb}</Text>
									</View>
								))}
							</View>
						) : null}

						{/* Overlay Video */}
						{overlayUri ? (
							<View style={styles.section}>
								<SectionHeader title="Annotated Video" />
								{overlayError && !isOverlayLoading ? <Text style={styles.overlayErr}>{overlayError}</Text> : null}
								<View style={styles.overlayWrap}>
									{overlayLocalUri ? (
										<AnalysisOverlayVideo
											key={`${overlayKey}-${overlayLocalUri}`}
											localUri={overlayLocalUri}
											style={styles.overlayVideo}
											onReady={() => { setIsOverlayLoading(false); setOverlayError(null) }}
											onError={() => { setOverlayError('Could not load overlay.'); setIsOverlayLoading(false) }}
										/>
									) : <View style={styles.overlayVideo} />}
									{isOverlayLoading ? (
										<View style={styles.overlaySpinner}>
											<ActivityIndicator size="large" color={colors.brand.orange} />
										</View>
									) : null}
								</View>
							</View>
						) : null}

						{/* Angles */}
						{analysisResult.angles_data?.frames?.length > 0 ? (
							<View style={styles.section}>
								<SectionHeader title="Angle Analysis" />
								<AngleGraph
									frameData={analysisResult.angles_data.frames.map((frame, idx) => {
										const toNum = (v: number | null | undefined) => typeof v === 'number' && Number.isFinite(v) ? v : 0
										return { frame_number: frame, elbow_angle: toNum(analysisResult.angles_data.elbow[idx]), knee_angle: toNum(analysisResult.angles_data.knee[idx]), release_angle: toNum(analysisResult.angles_data.wrist[idx]), body_alignment: 0 }
									})}
								/>
							</View>
						) : null}

						{/* CTAs */}
						<View style={styles.ctaRow}>
							<PrimaryButton
								label="Ask Coach J"
								icon="chatbubbles"
								variant="cyan"
								onPress={() => {
									hapticFeedback.medium()
									navigation.navigate('Coach J' as never)
								}}
								size="md"
							/>
							<PrimaryButton label="Analyze Again" icon="refresh" onPress={() => setAnalysisResult(null)} size="md" />
						</View>
					</View>
				) : null}

				<View style={styles.bottomPad} />
			</ScrollView>
		</SafeAreaView>
	)
}

const styles = StyleSheet.create({
	container: { flex: 1, backgroundColor: colors.bg.primary },
	scrollContent: { paddingBottom: spacing[4] },
	uploadSection: { padding: spacing.screenPadding, paddingTop: spacing[8] },
	uploadZone: {
		borderWidth: 2, borderStyle: 'dashed', borderColor: colors.brand.chromeMid, borderRadius: radius['2xl'],
		padding: spacing[8], alignItems: 'center',
	},
	uploadTitle: { ...typography.roles.headingSm, color: colors.text.primary, marginTop: spacing[4] },
	uploadHint: { ...typography.roles.caption, color: colors.text.tertiary, marginTop: spacing[1], marginBottom: spacing[6] },
	sideSelector: { width: '100%', marginBottom: spacing[6] },
	sideSelectorLabel: { ...typography.roles.caption, color: colors.text.secondary, marginBottom: spacing[2] },
	sidePills: { flexDirection: 'row', gap: spacing[2] },
	sidePill: { flex: 1, paddingVertical: spacing[2], borderRadius: radius.pill, borderWidth: 1, borderColor: colors.border.default, alignItems: 'center' },
	sidePillActive: { backgroundColor: colors.brand.orangeDim, borderColor: colors.brand.orange },
	sidePillText: { ...typography.roles.caption, color: colors.text.secondary },
	sidePillTextActive: { ...typography.roles.bodyStrong, color: colors.brand.orangeLight },
	uploadButtons: { width: '100%', gap: spacing[3] },
	processingSection: { flex: 1, alignItems: 'center', justifyContent: 'center', paddingVertical: spacing[20], paddingHorizontal: spacing.screenPadding },
	processingRing: { width: 120, height: 120, borderRadius: 60, borderWidth: 4, borderColor: colors.brand.orange, alignItems: 'center', justifyContent: 'center', marginBottom: spacing[8] },
	processingRingInner: { width: 100, height: 100, borderRadius: 50, borderWidth: 2, borderColor: colors.brand.orangeDim },
	processingLabel: { ...typography.roles.bodyStrong, color: colors.text.primary, textAlign: 'center' },
	processingHint: { ...typography.roles.caption, color: colors.text.tertiary, marginTop: spacing[2] },
	scoreHero: { alignItems: 'center', paddingVertical: spacing[10], paddingHorizontal: spacing.screenPadding, backgroundColor: colors.bg.void },
	scoreHeroLabel: { ...typography.roles.caption, color: colors.text.secondary, letterSpacing: typography.tracking.widest, textTransform: 'uppercase' as const, marginBottom: spacing[4] },
	scoreHeroDate: { ...typography.roles.caption, color: colors.text.tertiary, marginTop: spacing[3] },
	lowQualityBanner: {
		flexDirection: 'row', gap: spacing[3], alignItems: 'flex-start',
		margin: spacing.screenPadding, padding: spacing[4],
		borderRadius: radius.xl, borderWidth: 1, borderColor: colors.warning,
		backgroundColor: colors.bg.void,
	},
	lowQualityTitle: { ...typography.roles.bodyStrong, color: colors.text.primary },
	lowQualityText: { ...typography.roles.caption, color: colors.text.secondary, marginTop: spacing[1] },
	lowQualityHint: { ...typography.roles.caption, color: colors.text.tertiary, marginTop: spacing[2] },
	trackingChip: {
		flexDirection: 'row', alignItems: 'center', gap: spacing[2], flexWrap: 'wrap',
		marginHorizontal: spacing.screenPadding, marginTop: spacing[4],
		paddingVertical: spacing[2], paddingHorizontal: spacing[3],
		borderRadius: radius.pill, borderWidth: 1,
		backgroundColor: colors.bg.void,
	},
	trackingChipText: { ...typography.roles.caption, fontWeight: typography.weight.semibold, fontFamily: 'DMSansSemiBold' },
	trackingChipHint: {
		...typography.roles.caption, color: colors.text.tertiary,
		width: '100%', marginTop: spacing[1],
	},
	section: { paddingHorizontal: spacing.screenPadding, marginTop: spacing.sectionGap },
	metricsGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: spacing[3] },
	metricItem: { width: '47%' },
	phaseBar: { flexDirection: 'row', borderRadius: radius.sm, overflow: 'hidden', height: 36 },
	phaseBlock: { flex: 1, alignItems: 'center', justifyContent: 'center' },
	phaseText: { ...typography.roles.caption, color: colors.text.primary, fontWeight: typography.weight.semibold, fontFamily: 'DMSansSemiBold' },
	phaseInfo: { ...typography.roles.caption, color: colors.text.tertiary, marginTop: spacing[2] },
	feedbackCard: { flexDirection: 'row', alignItems: 'flex-start', gap: spacing[2], backgroundColor: colors.bg.secondary, borderRadius: radius.md, padding: spacing[3], marginBottom: spacing[2] },
	feedbackText: { flex: 1, fontSize: typography.size.sm, color: colors.text.primary, lineHeight: typography.size.sm * typography.lineHeight.normal, fontFamily: 'DMSansRegular' },
	overlayWrap: { position: 'relative', width: '100%' },
	overlayVideo: {
		width: '100%',
		height: 220,
		borderRadius: radius.lg,
		backgroundColor: semanticTokens.shadow.base,
		overflow: 'hidden',
	},
	overlaySpinner: {
		...StyleSheet.absoluteFillObject,
		alignItems: 'center',
		justifyContent: 'center',
		backgroundColor: `${semanticTokens.shadow.base}66`,
	},
	overlayErr: { fontSize: typography.size.xs, color: colors.error, marginBottom: spacing[2] },
	ctaRow: { flexDirection: 'row', gap: spacing[3], paddingHorizontal: spacing.screenPadding, marginTop: spacing.sectionGap },
	bottomPad: { height: spacing.tabBarHeight },
})
