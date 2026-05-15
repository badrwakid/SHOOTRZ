type EventHandler<T = unknown> = (payload?: T) => void

class EventBus {
	private listeners = new Map<string, Set<EventHandler>>()

	emit<T = unknown>(event: string, payload?: T): void {
		const handlers = this.listeners.get(event)
		if (!handlers || handlers.size === 0) {
			return
		}
		for (const handler of handlers) {
			handler(payload)
		}
	}

	on<T = unknown>(event: string, handler: EventHandler<T>): () => void {
		const current = this.listeners.get(event) ?? new Set<EventHandler>()
		current.add(handler as EventHandler)
		this.listeners.set(event, current)
		return () => this.off(event, handler)
	}

	off<T = unknown>(event: string, handler: EventHandler<T>): void {
		const handlers = this.listeners.get(event)
		if (!handlers) {
			return
		}
		handlers.delete(handler as EventHandler)
		if (handlers.size === 0) {
			this.listeners.delete(event)
		}
	}
}

export const eventBus = new EventBus()
