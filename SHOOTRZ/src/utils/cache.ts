/**
 * Simple in-memory cache for API responses.
 */

interface CacheEntry<T> {
	value: T
	expiry: number
}

class Cache {
	private cache: Map<string, CacheEntry<any>> = new Map()
	private defaultTTL: number = 5 * 60 * 1000 // 5 minutes

	get<T>(key: string): T | null {
		const entry = this.cache.get(key)
		if (!entry) {
			return null
		}

		if (Date.now() > entry.expiry) {
			this.cache.delete(key)
			return null
		}

		return entry.value as T
	}

	set<T>(key: string, value: T, ttl?: number): void {
		const expiry = Date.now() + (ttl || this.defaultTTL)
		this.cache.set(key, { value, expiry })
	}

	clear(): void {
		this.cache.clear()
	}

	delete(key: string): void {
		this.cache.delete(key)
	}
}

export const cache = new Cache()



