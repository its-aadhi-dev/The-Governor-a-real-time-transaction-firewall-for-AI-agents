export class EventClient {
    constructor({ basePath = "/api/v1/events" } = {}) {
        this.basePath = basePath;
        this.socket = null;
        this.transactionId = null;
        this.eventListeners = new Set();
        this.statusListeners = new Set();
    }

    onEvent(listener) {
        if (typeof listener !== "function") throw new TypeError("Event listener must be a function.");
        this.eventListeners.add(listener);
        return () => this.eventListeners.delete(listener);
    }

    onStatus(listener) {
        if (typeof listener !== "function") throw new TypeError("Status listener must be a function.");
        this.statusListeners.add(listener);
        return () => this.statusListeners.delete(listener);
    }

    emitEvent(event) {
        for (const listener of this.eventListeners) listener(event);
    }

    emitStatus(status) {
        for (const listener of this.statusListeners) listener(status);
    }

    connect(transactionId) {
        if (!transactionId) {
            throw new Error("transactionId is required.");
        }

        this.disconnect();
        this.transactionId = transactionId;

        const protocol = window.location.protocol === "https:"
            ? "wss:"
            : "ws:";
        const host = window.location.host;
        const url = `${protocol}//${host}${this.basePath}/${encodeURIComponent(transactionId)}`;

        this.socket = new WebSocket(url);

        this.socket.addEventListener("open", () => {
            this.emitStatus({ connected: true, transactionId });
        });

        this.socket.addEventListener("message", (message) => {
            try {
                this.emitEvent(JSON.parse(message.data));
            } catch (error) {
                console.error("Invalid event payload:", error);
            }
        });

        this.socket.addEventListener("close", () => {
            this.emitStatus({ connected: false, transactionId });
        });

        this.socket.addEventListener("error", (error) => {
            console.error("WebSocket error:", error);
            this.emitStatus({ connected: false, transactionId, error });
        });
    }

    disconnect() {
        if (this.socket) {
            this.socket.close();
            this.socket = null;
        }

        this.transactionId = null;
    }
}