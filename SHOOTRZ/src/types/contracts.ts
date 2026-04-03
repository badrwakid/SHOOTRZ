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
