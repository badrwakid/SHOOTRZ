import React, { useState, useRef, useMemo, useEffect } from 'react';
import {
	View,
	Text,
	StyleSheet,
	ScrollView,
	TouchableOpacity,
	Alert,
	ActivityIndicator,
} from 'react-native';
import { Video, ResizeMode } from 'expo-av';
import { LinearGradient } from 'expo-linear-gradient';
import { SafeAreaView } from 'react-native-safe-area-context';
import * as ImagePicker from 'expo-image-picker';
// Use legacy API for downloadAsync and cacheDirectory (Expo SDK 54 warning)
import * as FileSystem from 'expo-file-system/legacy';
import { Ionicons } from '@expo/vector-icons';
import { useAuth } from '../context/AuthContext';
import { storageService } from '../services/storage.service';
import { CameraRecorder } from '../components/CameraRecorder';
import { LoadingBasketball } from '../components/LoadingBasketball';
import { AngleGraph } from '../components/AngleGraph';
import { API_BASE_URL, apiService } from '../services/api.service';
import { SHOOTRZ_THEME } from '../constants/theme';
import { hapticFeedback } from '../utils/hapticFeedback';
import type { MVPMetric, MVPResultResponse } from '../types/contracts';

interface AnalysisResult extends MVPResultResponse {
	contract_version?: string;
	run_id: string;
	status: 'queued' | 'processing' | 'completed' | 'failed';
	overall_score: number;
	feedback_summary: string;
	feedback_bullets?: string[];
	metrics: MVPMetric[];
	score_components?: Array<{
		name: string;
		value: number;
		weight: number;
		unit?: string;
		explanation?: string;
	}>;
	shot_window: {
		start_frame?: number;
		crouch_frame?: number;
		release_frame?: number;
		end_frame?: number;
		confidence?: string;
		confidence_score?: number;
	};
	events?: {
		start?: {
			frame?: number | null;
			timestamp?: number | null;
			status?: string;
			confidence?: number;
			reason_codes?: string[];
		};
		crouch?: {
			frame?: number | null;
			timestamp?: number | null;
			status?: string;
			confidence?: number;
			reason_codes?: string[];
		};
		release?: {
			frame?: number | null;
			timestamp?: number | null;
			status?: string;
			confidence?: number;
			reason_codes?: string[];
		};
		end?: {
			frame?: number | null;
			timestamp?: number | null;
			status?: string;
			confidence?: number;
			reason_codes?: string[];
		};
	};
	angles_data: {
		frames: number[];
		timestamps: number[];
		elbow: Array<number | null>;
		knee: Array<number | null>;
		wrist: Array<number | null>;
	};
	artifacts: {
		overlay_video?: string | null;
		angles_csv?: string;
		report_json?: string;
		event_candidates?: string;
		warnings?: string;
	};
	key_frame_images?: {
		start?: string;
		crouch?: string;
		release?: string;
		end?: string;
	};
	diagnostics?: Record<string, unknown>;
	quality_warnings?: string[];
}

export const MVPAnalysisScreen: React.FC = () => {
	const { user } = useAuth();
	const [isAnalyzing, setIsAnalyzing] = useState(false);
	const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
	const [showCameraRecorder, setShowCameraRecorder] = useState(false);
	const [shootingSide, setShootingSide] = useState<'auto' | 'left' | 'right'>('auto');
	const lastRequestRef = useRef<string | null>(null);
	const overlayUri = useMemo(() => {
		if (!analysisResult?.artifacts?.overlay_video) return null;
		return `${API_BASE_URL}${analysisResult.artifacts.overlay_video}`;
	}, [analysisResult?.artifacts?.overlay_video]);
	const [isOverlayLoading, setIsOverlayLoading] = useState(false);
	const [overlayError, setOverlayError] = useState<string | null>(null);
	const [overlayLocalUri, setOverlayLocalUri] = useState<string | null>(null);
	const [overlayKey, setOverlayKey] = useState(0);

	const downloadOverlayToLocal = async (): Promise<string | null> => {
		if (!overlayUri || !analysisResult?.run_id) {
			setOverlayError('No overlay URL available.');
			return null;
		}
		try {
			setIsOverlayLoading(true);
			const cacheDir = (FileSystem as any).cacheDirectory ?? (FileSystem as any).documentDirectory ?? '';
			const targetPath = `${cacheDir}overlay_${analysisResult.run_id}.mp4`;
			const res = await FileSystem.downloadAsync(overlayUri, targetPath);
			setOverlayLocalUri(res.uri);
			setOverlayError(null);
			return res.uri;
		} catch (err) {
			console.error('Overlay download error', err);
			setOverlayError('Unable to load overlay. Try “Open in browser”.');
			return null;
		} finally {
			setIsOverlayLoading(false);
		}
	};

	useEffect(() => {
		// Load overlay once per source (prefer cached local copy)
		let canceled = false;
		const loadOverlay = async () => {
			if (!overlayUri) return;
			setOverlayError(null);
			setIsOverlayLoading(true);
			setOverlayLocalUri(null);
			setOverlayKey(prev => prev + 1);

			const localUri = await downloadOverlayToLocal();
			if (canceled) return;

			if (localUri) {
				setOverlayLocalUri(localUri);
				setOverlayError(null);
			} else {
				setOverlayError('Could not load overlay. Please retry.');
			}
			setIsOverlayLoading(false);
		};

		loadOverlay();
		return () => {
			canceled = true;
		};
		// eslint-disable-next-line react-hooks/exhaustive-deps
	}, [overlayUri]);

	const pickVideo = async () => {
		try {
			const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();

			if (status !== 'granted') {
				Alert.alert('Permission Required', 'Camera roll access is required to select videos');
				return;
			}

			const result = await ImagePicker.launchImageLibraryAsync({
				mediaTypes: 'videos',
				allowsEditing: false,
				quality: 1,
				videoMaxDuration: 30,
			});

			if (!result.canceled && result.assets[0]) {
				await handleAnalyzeVideo(result.assets[0].uri);
			}
		} catch (error) {
			console.error('Error picking video:', error);
			Alert.alert('Error', 'Failed to select video. Please try again.');
		}
	};

	const recordVideo = () => {
		setShowCameraRecorder(true);
		hapticFeedback.medium();
	};

	const handleVideoRecorded = async (videoUri: string) => {
		setShowCameraRecorder(false);
		await handleAnalyzeVideo(videoUri);
	};

	const handleCameraCancel = () => {
		setShowCameraRecorder(false);
	};

	const handleAnalyzeVideo = async (videoUri: string) => {
		if (isAnalyzing || lastRequestRef.current === videoUri) {
			console.log('Duplicate request prevented:', videoUri);
			return;
		}

		lastRequestRef.current = videoUri;
		setIsAnalyzing(true);
		setAnalysisResult(null);
		setOverlayError(null);
		setIsOverlayLoading(true);
		setOverlayLocalUri(null);

		try {
			// Call MVP API endpoint
			const uploadResponse = await apiService.analyzeMVP(videoUri, shootingSide);

			if (uploadResponse.job_id) {
				// Poll for results
				let pollCount = 0;
				const maxPolls = 120; // 2 minutes timeout

				while (pollCount < maxPolls) {
					await new Promise(resolve => setTimeout(resolve, 1000));

					const resultResponse = await apiService.getMVPResult(uploadResponse.job_id);

					if (resultResponse.status === 'completed') {
						// Validate and sanitize the response
						const validatedResult: AnalysisResult = {
							...resultResponse,
							run_id: resultResponse.run_id ?? '',
							status: resultResponse.status ?? 'completed',
							overall_score: resultResponse.overall_score ?? 0,
							feedback_summary: resultResponse.feedback_summary || 'Analysis completed',
							feedback_bullets: Array.isArray(resultResponse.feedback_bullets) ? resultResponse.feedback_bullets : [],
							metrics: Array.isArray(resultResponse.metrics) ? resultResponse.metrics : [],
							score_components: Array.isArray(resultResponse.score_components) ? resultResponse.score_components : [],
							shot_window: resultResponse.shot_window || {},
							events: resultResponse.events || {},
							angles_data: resultResponse.angles_data || { frames: [], timestamps: [], elbow: [], knee: [], wrist: [] },
							artifacts: resultResponse.artifacts || {},
							key_frame_images: resultResponse.key_frame_images || {},
							diagnostics: resultResponse.diagnostics || {},
						};
						
						setAnalysisResult(validatedResult);
						hapticFeedback.success();
						setOverlayError(null);
						setIsOverlayLoading(true);

						// Persist analysis for streaks/dashboard
						try {
							const findMetricValue = (key: string) => {
								const metric = validatedResult.metrics.find(m => m.name?.toLowerCase().includes(key));
								return Number.isFinite(metric?.value) ? (metric?.value as number) : 0;
							};
							const findComponentValue = (key: string) => {
								const component = validatedResult.score_components?.find(c =>
									c.name?.toLowerCase().includes(key),
								)
								return Number.isFinite(component?.value) ? (component?.value as number) : 0
							}
							const analysisRecord = {
								id: `${Date.now()}`,
								userId: user?.id || 'local',
								timestamp: new Date().toISOString(),
								runId: validatedResult.run_id || undefined,
								scores: {
									elbow: findMetricValue('elbow'),
									balance: findComponentValue('balance'),
									release: findComponentValue('release'),
									alignment: findComponentValue('loading'),
									total: validatedResult.overall_score ?? 0,
								},
								feedback: validatedResult.feedback_bullets?.length
									? validatedResult.feedback_bullets
									: validatedResult.feedback_summary
										? [validatedResult.feedback_summary]
										: [],
								angles: {
									elbow: findMetricValue('elbow'),
									knee: findMetricValue('knee'),
									release: findMetricValue('wrist'),
									bodyAlignment: findComponentValue('balance'),
								},
								mvp: {
									scoreComponents: validatedResult.score_components?.map(c => ({
										name: c.name,
										value: c.value,
										weight: c.weight,
									})),
									keyFrameImages: validatedResult.key_frame_images,
									shotWindow: validatedResult.shot_window,
									events: validatedResult.events,
									diagnostics: validatedResult.diagnostics,
								},
							};
							storageService.saveAnalysisResult(analysisRecord as any).catch(err => {
								console.error('Failed to persist analysis history', err);
							});
						} catch (persistErr) {
							console.error('Error saving analysis history', persistErr);
						}
						return;
					}

					if (resultResponse.status === 'failed') {
						const errorMsg = resultResponse.error || resultResponse.error_detail || 'Analysis failed';
						throw new Error(errorMsg);
					}

					pollCount++;
				}

				throw new Error('Analysis timed out. Please try again.');
			} else {
				throw new Error('Failed to start analysis');
			}
		} catch (error: any) {
			console.error('Analysis error:', error);
			hapticFeedback.error();
			setIsOverlayLoading(false);
			
			// User-friendly error messages
			let errorMessage = error.message || 'Failed to analyze video. Please try again.';
			
			if (errorMessage.includes('timeout')) {
				errorMessage = 'Analysis took too long. Please try with a shorter video (3-10 seconds recommended).';
			} else if (errorMessage.includes('Network') || errorMessage.includes('Could not reach')) {
				errorMessage = 'Cannot connect to analysis server. Please check your connection.';
			} else if (errorMessage.includes('pose')) {
				errorMessage = 'Could not detect your form. Please ensure you are clearly visible and well-lit.';
			}
			
			Alert.alert('Analysis Failed', errorMessage);
		} finally {
			setIsAnalyzing(false);
			setTimeout(() => {
				lastRequestRef.current = null;
			}, 5000);
		}
	};

	const getVerdictColor = (verdict: string) => {
		if (verdict === 'Good') return SHOOTRZ_THEME.colors.success;
		if (verdict === 'Needs Work') return SHOOTRZ_THEME.colors.warning;
		return SHOOTRZ_THEME.colors.textSecondary;
	};

	const formatFrameValue = (value?: number) => {
		return Number.isFinite(value) ? value : '--';
	};

	if (showCameraRecorder) {
		return (
			<CameraRecorder
				onVideoRecorded={handleVideoRecorded}
				onCancel={handleCameraCancel}
				maxDuration={30}
			/>
		);
	}

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
				style={styles.backgroundGradient}
			>
				<ScrollView
					style={styles.scrollView}
					showsVerticalScrollIndicator={false}
					contentContainerStyle={styles.scrollContent}
				>
					{/* Header */}
					<View style={styles.header}>
						<View style={styles.headerContent}>
							<View style={styles.headerIconContainer}>
								<Ionicons name="analytics" size={28} color={SHOOTRZ_THEME.colors.primary} />
							</View>
							<View style={styles.headerTextContainer}>
								<Text style={styles.title}>MVP Shot Analysis</Text>
								<Text style={styles.subtitle}>
									Deterministic biomechanics analysis with 3 core metrics
								</Text>
							</View>
						</View>
					</View>

					{!analysisResult ? (
						<View style={styles.recordingSection}>
							<View style={styles.placeholder}>
								<View style={styles.placeholderIconContainer}>
									<Ionicons name="analytics" size={64} color={SHOOTRZ_THEME.colors.primary} />
								</View>
								<Text style={styles.placeholderTitle}>Upload or Record Your Shot</Text>
								<Text style={styles.placeholderText}>
									Get biomechanically accurate analysis with:
								</Text>
								<View style={styles.featuresList}>
									<View style={styles.featureItem}>
										<Ionicons name="checkmark-circle" size={18} color={SHOOTRZ_THEME.colors.success} />
										<Text style={styles.featureText}>Elbow extension at release</Text>
									</View>
									<View style={styles.featureItem}>
										<Ionicons name="checkmark-circle" size={18} color={SHOOTRZ_THEME.colors.success} />
										<Text style={styles.featureText}>Knee bend depth</Text>
									</View>
									<View style={styles.featureItem}>
										<Ionicons name="checkmark-circle" size={18} color={SHOOTRZ_THEME.colors.success} />
										<Text style={styles.featureText}>Wrist follow-through</Text>
									</View>
								</View>

								{isAnalyzing ? (
									<LoadingBasketball message="Analyzing your form..." size="large" />
								) : (
									<View style={styles.actionButtonsContainer}>
										<View style={styles.sideSelector}>
											<Text style={styles.sideSelectorLabel}>Shooting Side</Text>
											<View style={styles.sideSelectorButtons}>
												{(['auto', 'left', 'right'] as const).map(side => (
													<TouchableOpacity
														key={side}
														style={[
															styles.sideButton,
															shootingSide === side && styles.sideButtonActive,
														]}
														onPress={() => setShootingSide(side)}
													>
														<Text
															style={[
																styles.sideButtonText,
																shootingSide === side && styles.sideButtonTextActive,
															]}
														>
															{side === 'auto' ? 'Auto' : side === 'left' ? 'Left' : 'Right'}
														</Text>
													</TouchableOpacity>
												))}
											</View>
										</View>
										<TouchableOpacity
											onPress={recordVideo}
											style={styles.actionButton}
											activeOpacity={0.8}
										>
											<LinearGradient
												colors={[SHOOTRZ_THEME.colors.primary, SHOOTRZ_THEME.colors.primaryDark]}
												start={{ x: 0, y: 0 }}
												end={{ x: 1, y: 1 }}
												style={styles.actionButtonGradient}
											>
												<Ionicons name="videocam" size={24} color="#fff" />
												<Text style={styles.actionButtonText}>Record Video</Text>
											</LinearGradient>
										</TouchableOpacity>

										<TouchableOpacity
											onPress={pickVideo}
											style={styles.actionButton}
											activeOpacity={0.8}
										>
											<LinearGradient
												colors={[SHOOTRZ_THEME.colors.secondary, SHOOTRZ_THEME.colors.secondaryDark]}
												start={{ x: 0, y: 0 }}
												end={{ x: 1, y: 1 }}
												style={styles.actionButtonGradient}
											>
												<Ionicons name="cloud-upload" size={24} color="#fff" />
												<Text style={styles.actionButtonText}>Upload Video</Text>
											</LinearGradient>
										</TouchableOpacity>
									</View>
								)}
							</View>
						</View>
					) : (
						<View style={styles.resultsSection}>
							{/* Overall Score */}
							<View style={styles.scoreSection}>
								<Text style={styles.sectionTitle}>Overall Performance</Text>
								<View style={styles.scoreDisplay}>
									<Text style={styles.scoreValue}>{analysisResult.overall_score}</Text>
									<Text style={styles.scoreMax}>/100</Text>
								</View>
								<Text style={styles.feedbackSummary}>{analysisResult.feedback_summary}</Text>
							{analysisResult.quality_warnings && analysisResult.quality_warnings.length > 0 ? (
								<Text style={styles.overlayError}>
									Warnings: {analysisResult.quality_warnings.join(', ')}
								</Text>
							) : null}
							</View>

							{/* Three Core Metrics */}
							<View style={styles.metricsSection}>
								<Text style={styles.sectionTitle}>Core Shooting Metrics</Text>
								{analysisResult.metrics && analysisResult.metrics.length > 0 ? (
									analysisResult.metrics.map((metric, index) => (
										<View key={index} style={styles.metricCard}>
											<View style={styles.metricHeader}>
												<Text style={styles.metricName}>
													{metric.name ? metric.name.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) : 'Unknown Metric'}
												</Text>
												<View style={[
													styles.verdictBadge,
													{ backgroundColor: getVerdictColor(metric.verdict || 'Low Confidence') + '20' }
												]}>
													<Text style={[styles.verdictText, { color: getVerdictColor(metric.verdict || 'Low Confidence') }]}>
														{metric.verdict || 'Unknown'}
													</Text>
												</View>
											</View>
											<Text style={styles.metricValue}>
												{metric.value != null ? metric.value.toFixed(1) : '--'} {metric.unit || ''}
											</Text>
											<Text style={styles.metricExplanation}>{metric.explanation || 'No explanation available'}</Text>
											<View style={styles.confidenceBar}>
												<View
													style={[
														styles.confidenceFill,
														{
															width: `${(metric.confidence != null ? metric.confidence : 0) * 100}%`,
															backgroundColor: SHOOTRZ_THEME.colors.primary
														}
													]}
												/>
											</View>
											<Text style={styles.confidenceText}>
												Confidence: {metric.confidence != null ? (metric.confidence * 100).toFixed(0) : '0'}%
											</Text>
										</View>
									))
								) : (
									<View style={styles.metricCard}>
										<Text style={styles.metricName}>No metrics available</Text>
									</View>
								)}
							</View>

							{/* Annotated video */}
							{overlayUri && (
								<View style={styles.anglesSection}>
									<Text style={styles.sectionTitle}>Annotated Video</Text>
									{overlayError && !isOverlayLoading ? (
										<Text style={styles.overlayError}>
											Could not load overlay video. {overlayError}
										</Text>
									) : null}
									<View style={styles.overlayWrapper}>
										{overlayLocalUri ? (
											<Video
												key={`${overlayKey}`}
												source={{ uri: overlayLocalUri }}
												style={styles.overlayVideo}
												useNativeControls
												resizeMode={ResizeMode.CONTAIN}
												shouldPlay={false}
												isLooping
												onLoadStart={() => {
													setIsOverlayLoading(true);
													setOverlayError(null);
												}}
												onLoad={() => {
													setIsOverlayLoading(false);
													setOverlayError(null);
												}}
												onError={err => {
													console.error('Overlay video error', err);
													setOverlayError('Could not load overlay. Please retry.');
													setIsOverlayLoading(false);
												}}
											/>
										) : (
											<View style={styles.overlayVideo} />
										)}
										{isOverlayLoading && (
											<View style={styles.overlaySpinner}>
												<ActivityIndicator size="large" color={SHOOTRZ_THEME.colors.primary} />
												<Text style={styles.overlayLoadingText}>Loading overlay…</Text>
											</View>
										)}
									</View>
									<Text style={styles.overlayCaption}>
										Overlay shows detected joints and shot phases for visual verification.
									</Text>
								</View>
							)}

							{/* Angle Graphs */}
							{analysisResult.angles_data && analysisResult.angles_data.frames.length > 0 && (
								<View style={styles.anglesSection}>
									<Text style={styles.sectionTitle}>Angle Analysis</Text>
									<AngleGraph
										frameData={analysisResult.angles_data.frames.map((frame, idx) => {
											const elbow = analysisResult.angles_data.elbow[idx]
											const knee = analysisResult.angles_data.knee[idx]
											const wrist = analysisResult.angles_data.wrist[idx]
											const toNum = (v: number | null | undefined) =>
												typeof v === 'number' && Number.isFinite(v) ? v : 0
											return {
												frame_number: frame,
												elbow_angle: toNum(elbow),
												knee_angle: toNum(knee),
												release_angle: toNum(wrist),
												body_alignment: 0,
											}
										})}
									/>
									<View style={styles.shotWindowInfo}>
										<Text style={styles.shotWindowText}>
											Shot Window: Frame {formatFrameValue(analysisResult.shot_window?.start_frame)} - {formatFrameValue(analysisResult.shot_window?.end_frame)}
										</Text>
										<Text style={styles.shotWindowText}>
											Release: Frame {formatFrameValue(analysisResult.shot_window?.release_frame)}
										</Text>
									</View>
								</View>
							)}

							{/* Analyze Again Button */}
							<TouchableOpacity
								onPress={() => setAnalysisResult(null)}
								style={styles.analyzeAgainButton}
							>
								<LinearGradient
									colors={[SHOOTRZ_THEME.colors.primary, SHOOTRZ_THEME.colors.secondary]}
									start={{ x: 0, y: 0 }}
									end={{ x: 1, y: 0 }}
									style={styles.analyzeAgainGradient}
								>
									<Ionicons name="refresh" size={20} color="#fff" style={{ marginRight: 8 }} />
									<Text style={styles.analyzeAgainText}>Analyze Another Shot</Text>
								</LinearGradient>
							</TouchableOpacity>
						</View>
					)}
				</ScrollView>
			</LinearGradient>
		</SafeAreaView>
	);
};

const styles = StyleSheet.create({
	container: {
		flex: 1,
		backgroundColor: SHOOTRZ_THEME.colors.background,
	},
	backgroundGradient: {
		flex: 1,
	},
	scrollView: {
		flex: 1,
	},
	scrollContent: {
		paddingBottom: SHOOTRZ_THEME.spacing.xxl,
	},
	header: {
		padding: SHOOTRZ_THEME.spacing.lg,
		paddingTop: SHOOTRZ_THEME.spacing.xl,
		backgroundColor: SHOOTRZ_THEME.colors.surface + 'F0',
		borderBottomWidth: 2,
		borderBottomColor: SHOOTRZ_THEME.colors.primary + '30',
	},
	headerContent: {
		flexDirection: 'row',
		alignItems: 'center',
	},
	headerIconContainer: {
		width: 48,
		height: 48,
		borderRadius: 24,
		backgroundColor: SHOOTRZ_THEME.colors.primary + '20',
		alignItems: 'center',
		justifyContent: 'center',
		marginRight: SHOOTRZ_THEME.spacing.md,
	},
	headerTextContainer: {
		flex: 1,
	},
	title: {
		...SHOOTRZ_THEME.typography.heading2,
		fontSize: 22,
		marginBottom: 4,
	},
	subtitle: {
		...SHOOTRZ_THEME.typography.bodySmall,
		color: SHOOTRZ_THEME.colors.textSecondary,
		fontSize: 13,
	},
	recordingSection: {
		flex: 1,
		padding: SHOOTRZ_THEME.spacing.lg,
	},
	placeholder: {
		flex: 1,
		backgroundColor: SHOOTRZ_THEME.colors.surface,
		borderRadius: SHOOTRZ_THEME.borderRadius.xl,
		padding: SHOOTRZ_THEME.spacing.xxl,
		alignItems: 'center',
		justifyContent: 'center',
		borderWidth: 2,
		borderColor: SHOOTRZ_THEME.colors.surfaceElevated,
	},
	placeholderIconContainer: {
		marginBottom: SHOOTRZ_THEME.spacing.lg,
	},
	placeholderTitle: {
		...SHOOTRZ_THEME.typography.heading2,
		marginBottom: SHOOTRZ_THEME.spacing.md,
		textAlign: 'center',
	},
	placeholderText: {
		...SHOOTRZ_THEME.typography.body,
		textAlign: 'center',
		marginBottom: SHOOTRZ_THEME.spacing.lg,
		color: SHOOTRZ_THEME.colors.textSecondary,
	},
	featuresList: {
		width: '100%',
		marginTop: SHOOTRZ_THEME.spacing.md,
		marginBottom: SHOOTRZ_THEME.spacing.xl,
	},
	featureItem: {
		flexDirection: 'row',
		alignItems: 'center',
		marginBottom: SHOOTRZ_THEME.spacing.sm,
	},
	featureText: {
		...SHOOTRZ_THEME.typography.bodySmall,
		marginLeft: SHOOTRZ_THEME.spacing.sm,
		color: SHOOTRZ_THEME.colors.textPrimary,
	},
	actionButtonsContainer: {
		width: '100%',
		gap: SHOOTRZ_THEME.spacing.md,
	},
	sideSelector: {
		width: '100%',
		padding: SHOOTRZ_THEME.spacing.md,
		borderRadius: SHOOTRZ_THEME.borderRadius.lg,
		borderWidth: 1,
		borderColor: SHOOTRZ_THEME.colors.surfaceElevated,
		backgroundColor: SHOOTRZ_THEME.colors.surfaceElevated + '40',
	},
	sideSelectorLabel: {
		...SHOOTRZ_THEME.typography.body,
		marginBottom: SHOOTRZ_THEME.spacing.sm,
		color: SHOOTRZ_THEME.colors.textSecondary,
	},
	sideSelectorButtons: {
		flexDirection: 'row',
		gap: SHOOTRZ_THEME.spacing.sm,
	},
	sideButton: {
		flex: 1,
		paddingVertical: SHOOTRZ_THEME.spacing.sm,
		borderRadius: SHOOTRZ_THEME.borderRadius.md,
		borderWidth: 1,
		borderColor: SHOOTRZ_THEME.colors.surfaceElevated,
		alignItems: 'center',
	},
	sideButtonActive: {
		backgroundColor: SHOOTRZ_THEME.colors.primary + '20',
		borderColor: SHOOTRZ_THEME.colors.primary,
	},
	sideButtonText: {
		...SHOOTRZ_THEME.typography.bodySmall,
		color: SHOOTRZ_THEME.colors.textSecondary,
	},
	sideButtonTextActive: {
		color: SHOOTRZ_THEME.colors.primary,
		fontWeight: '700',
	},
	actionButton: {
		borderRadius: SHOOTRZ_THEME.borderRadius.xl,
		overflow: 'hidden',
		shadowColor: '#000',
		shadowOffset: { width: 0, height: 4 },
		shadowOpacity: 0.2,
		shadowRadius: 8,
		elevation: 6,
	},
	actionButtonGradient: {
		padding: SHOOTRZ_THEME.spacing.lg,
		flexDirection: 'row',
		alignItems: 'center',
		justifyContent: 'center',
		gap: SHOOTRZ_THEME.spacing.sm,
	},
	actionButtonText: {
		...SHOOTRZ_THEME.typography.button,
		color: '#fff',
		fontSize: 16,
	},
	resultsSection: {
		padding: SHOOTRZ_THEME.spacing.lg,
	},
	scoreSection: {
		backgroundColor: SHOOTRZ_THEME.colors.surface,
		borderRadius: SHOOTRZ_THEME.borderRadius.xl,
		padding: SHOOTRZ_THEME.spacing.xl,
		alignItems: 'center',
		marginBottom: SHOOTRZ_THEME.spacing.lg,
		borderWidth: 2,
		borderColor: SHOOTRZ_THEME.colors.primary + '30',
	},
	sectionTitle: {
		...SHOOTRZ_THEME.typography.heading3,
		fontSize: 20,
		marginBottom: SHOOTRZ_THEME.spacing.md,
	},
	scoreDisplay: {
		flexDirection: 'row',
		alignItems: 'baseline',
		marginVertical: SHOOTRZ_THEME.spacing.lg,
	},
	scoreValue: {
		fontSize: 64,
		fontWeight: 'bold',
		color: SHOOTRZ_THEME.colors.primary,
	},
	scoreMax: {
		fontSize: 24,
		color: SHOOTRZ_THEME.colors.textSecondary,
		marginLeft: 4,
	},
	feedbackSummary: {
		...SHOOTRZ_THEME.typography.body,
		textAlign: 'center',
		color: SHOOTRZ_THEME.colors.textSecondary,
	},
	metricsSection: {
		marginBottom: SHOOTRZ_THEME.spacing.lg,
	},
	metricCard: {
		backgroundColor: SHOOTRZ_THEME.colors.surface,
		borderRadius: SHOOTRZ_THEME.borderRadius.lg,
		padding: SHOOTRZ_THEME.spacing.lg,
		marginBottom: SHOOTRZ_THEME.spacing.md,
		borderWidth: 1,
		borderColor: SHOOTRZ_THEME.colors.surfaceElevated,
	},
	metricHeader: {
		flexDirection: 'row',
		justifyContent: 'space-between',
		alignItems: 'center',
		marginBottom: SHOOTRZ_THEME.spacing.sm,
	},
	metricName: {
		...SHOOTRZ_THEME.typography.heading3,
		fontSize: 18,
	},
	verdictBadge: {
		paddingHorizontal: SHOOTRZ_THEME.spacing.md,
		paddingVertical: SHOOTRZ_THEME.spacing.xs,
		borderRadius: SHOOTRZ_THEME.borderRadius.md,
	},
	verdictText: {
		...SHOOTRZ_THEME.typography.bodySmall,
		fontWeight: '600',
		fontSize: 12,
	},
	metricValue: {
		fontSize: 32,
		fontWeight: 'bold',
		color: SHOOTRZ_THEME.colors.primary,
		marginBottom: SHOOTRZ_THEME.spacing.sm,
	},
	metricExplanation: {
		...SHOOTRZ_THEME.typography.body,
		color: SHOOTRZ_THEME.colors.textSecondary,
		marginBottom: SHOOTRZ_THEME.spacing.sm,
	},
	confidenceBar: {
		height: 4,
		backgroundColor: SHOOTRZ_THEME.colors.surfaceElevated,
		borderRadius: 2,
		overflow: 'hidden',
		marginBottom: SHOOTRZ_THEME.spacing.xs,
	},
	confidenceFill: {
		height: '100%',
	},
	confidenceText: {
		...SHOOTRZ_THEME.typography.bodySmall,
		color: SHOOTRZ_THEME.colors.textSecondary,
		fontSize: 11,
	},
	anglesSection: {
		marginBottom: SHOOTRZ_THEME.spacing.lg,
	},
	overlayVideo: {
		width: '100%',
		height: 220,
		borderRadius: SHOOTRZ_THEME.borderRadius.lg,
		backgroundColor: '#000',
		overflow: 'hidden',
	},
	overlayWrapper: {
		position: 'relative',
		width: '100%',
	},
	overlaySpinner: {
		position: 'absolute',
		top: 0,
		left: 0,
		right: 0,
		bottom: 0,
		alignItems: 'center',
		justifyContent: 'center',
		backgroundColor: '#00000066',
	},
	overlayLoading: {
		flexDirection: 'row',
		alignItems: 'center',
		marginTop: SHOOTRZ_THEME.spacing.sm,
	},
	overlayLoadingText: {
		...SHOOTRZ_THEME.typography.bodySmall,
		color: SHOOTRZ_THEME.colors.textSecondary,
		marginLeft: SHOOTRZ_THEME.spacing.xs,
	},
	overlayCaption: {
		...SHOOTRZ_THEME.typography.bodySmall,
		color: SHOOTRZ_THEME.colors.textSecondary,
		marginTop: SHOOTRZ_THEME.spacing.sm,
	},
	overlayError: {
		...SHOOTRZ_THEME.typography.bodySmall,
		color: SHOOTRZ_THEME.colors.error,
		marginBottom: SHOOTRZ_THEME.spacing.xs,
	},
	shotWindowInfo: {
		backgroundColor: SHOOTRZ_THEME.colors.surface,
		borderRadius: SHOOTRZ_THEME.borderRadius.md,
		padding: SHOOTRZ_THEME.spacing.md,
		marginTop: SHOOTRZ_THEME.spacing.md,
	},
	shotWindowText: {
		...SHOOTRZ_THEME.typography.bodySmall,
		color: SHOOTRZ_THEME.colors.textSecondary,
		marginBottom: 4,
	},
	analyzeAgainButton: {
		marginTop: SHOOTRZ_THEME.spacing.xl,
		borderRadius: SHOOTRZ_THEME.borderRadius.xl,
		overflow: 'hidden',
	},
	analyzeAgainGradient: {
		flexDirection: 'row',
		padding: SHOOTRZ_THEME.spacing.lg,
		alignItems: 'center',
		justifyContent: 'center',
	},
	analyzeAgainText: {
		...SHOOTRZ_THEME.typography.button,
		color: '#fff',
		fontSize: 16,
	},
});
