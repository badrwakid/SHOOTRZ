export interface HealthResponse {
	status: string
	service: string
	version: string
	timestamp: string
	uptime: number
}

export interface MVPMetric {
	name: string
	value: number
	unit: string
	verdict: 'Good' | 'Needs Work' | 'Low Confidence'
	explanation: string
	confidence: number
	frame_range?: [number, number]
}

export interface MVPScoreComponent {
	name: string
	value: number
	unit?: string
	weight: number
	explanation?: string
}

export interface MVPEventAlternative {
	frame_id: number
	score: number
	kind: string
}

export interface MVPEvent {
	frame?: number | null
	timestamp?: number | null
	status?: 'detected' | 'estimated' | 'missing' | string
	confidence?: number
	reason_codes?: string[]
	alternatives?: MVPEventAlternative[]
}

export interface MVPResultResponse {
	status: 'queued' | 'processing' | 'completed' | 'failed'
	contract_version?: string
	run_id?: string
	overall_score?: number
	feedback_summary?: string
	feedback_bullets?: string[]
	metrics?: MVPMetric[]
	score_components?: MVPScoreComponent[]
	shot_window?: {
		start_frame?: number
		crouch_frame?: number
		release_frame?: number
		end_frame?: number
		confidence?: string
		confidence_score?: number
		method?: string
	}
	events?: {
		start?: MVPEvent
		crouch?: MVPEvent
		release?: MVPEvent
		end?: MVPEvent
	}
	angles_data?: {
		frames: number[]
		timestamps: number[]
		elbow: Array<number | null>
		knee: Array<number | null>
		wrist: Array<number | null>
	}
	artifacts?: {
		overlay_video?: string | null
		angles_csv?: string
		report_json?: string
		event_candidates?: string
		event_confidence?: string
		feature_table?: string
		signals_smoothed?: string
		warnings?: string
	}
	key_frame_images?: {
		start?: string
		crouch?: string
		release?: string
		end?: string
	}
	diagnostics?: Record<string, unknown>
	quality_warnings?: string[]
	error?: string
	error_detail?: string
	error_type?: string
}

export interface HistoryMetric {
	id?: string
	metric_name: string
	value: number
	unit?: string
	confidence?: number
	phase?: string
	frame_idx?: number
	created_at?: string
}

export interface HistorySession {
	session_id: string
	timestamp: string
	title?: string | null
	date: string
	shot_count: number
	average_score?: number | null
	metrics: HistoryMetric[]
	angle?: string | null
	fps?: number | null
	device?: string | null
}

export interface HistoryResponse {
	user_id: string
	sessions: HistorySession[]
	total: number
	limit?: number
	offset?: number
}

export interface HistoryStatsResponse {
	total_sessions: number
	total_shots: number
	average_score: number | null
	best_score: number | null
	improvement_percentage: number | null
	consistency_score: number | null
}

export interface ChatMessageDto {
	role: 'user' | 'assistant'
	content: string
}

export interface ChatRequestDto {
	messages: ChatMessageDto[]
	includeRawArtifacts?: boolean
	model?: string
}

export interface ChatResponseDto {
	assistant_message: string
	context_used: Record<string, unknown>
	model: string
	usage?: Record<string, unknown>
}

export interface ChatStreamDelta {
	text: string
}

export interface ChatStreamDone {
	context_used: Record<string, unknown>
	model: string
	usage?: Record<string, unknown>
}

export interface ChatStreamError {
	message: string
}

export interface StreamCallbacks {
	onChunk: (text: string) => void
	onDone: (metadata: ChatStreamDone) => void
	onError: (error: Error) => void
}

// ---------------------------------------------------------------------------
// New DB-backed types (Supabase schema)
// ---------------------------------------------------------------------------

export interface UserProfile {
	id: string
	userId: string
	primaryGoal?: string
	trainingFrequency?: string
	preferredDrillDuration?: number
	age?: number
	heightCm?: number
	weightKg?: number
	dominantHand?: 'left' | 'right'
	yearsPlaying?: number
	notificationsEnabled?: boolean
	coachingStyle?: 'encouraging' | 'direct' | 'analytical' | 'balanced'
	createdAt: string
	updatedAt: string
}

export interface AnalysisSummary {
	id: string
	sessionId: string
	userId: string
	overallScore?: number
	shotCount?: number
	elbowAngleScore?: number
	kneeBendScore?: number
	releaseAngleScore?: number
	followThroughScore?: number
	balanceScore?: number
	elbowAngleValue?: number
	kneeBendValue?: number
	releaseAngleValue?: number
	phasesDetected?: string[]
	dominantPhaseIssue?: string
	topStrengths?: string[]
	topImprovements?: string[]
	scoreTier?: 'elite' | 'great' | 'good' | 'fair' | 'poor'
	createdAt: string
}

export interface ChatHistoryMessage {
	id: string
	userId: string
	role: 'user' | 'assistant'
	content: string
	sessionId?: string
	modelUsed?: string
	createdAt: string
}

export interface DrillCompletion {
	id: string
	userId: string
	drillId: string
	drillName: string
	completedAt: string
	durationSeconds?: number
	userRating?: number
}

export interface WorkoutProgress {
	id: string
	userId: string
	workoutId: string
	workoutName: string
	status: 'not_started' | 'in_progress' | 'completed'
	drillsCompleted: number
	drillsTotal: number
	startedAt?: string
	completedAt?: string
}

export interface UserStreak {
	currentStreak: number
	longestStreak: number
	lastActivityDate?: string
}

export interface UserStats {
	totalSessions: number
	avgScore?: number
	bestScore?: number
	totalShots?: number
	currentStreak: number
	longestStreak: number
	lastSessionDate?: string
}
