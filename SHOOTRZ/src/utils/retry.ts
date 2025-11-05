/**
 * Retry utility for failed API calls.
 */

export interface RetryOptions {
	maxAttempts?: number
	delay?: number
	backoff?: number
	onRetry?: (attempt: number, error: Error) => void
}

export async function retry<T>(
	fn: () => Promise<T>,
	options: RetryOptions = {}
): Promise<T> {
	const {
		maxAttempts = 3,
		delay = 1000,
		backoff = 2,
		onRetry,
	} = options

	let lastError: Error
	let currentDelay = delay

	for (let attempt = 1; attempt <= maxAttempts; attempt++) {
		try {
			return await fn()
		} catch (error) {
			lastError = error as Error

			if (attempt < maxAttempts) {
				if (onRetry) {
					onRetry(attempt, lastError)
				}

				await new Promise((resolve) => setTimeout(resolve, currentDelay))
				currentDelay *= backoff
			}
		}
	}

	throw lastError!
}



