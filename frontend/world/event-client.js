export class EventClient {
    constructor({
        basePath = "/api/v1/events",
        onEvent = () => {},
        onStatus = () => {},
    } = {}) {
        this.basePath = basePath;
        this.onEvent = onEvent;
        this.onStatus = onStatus;
        this.socket = null;
        this.transactionId = null;
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
            this.onStatus({ connected: true, transactionId });
        });

        this.socket.addEventListener("message", (message) => {
            try {
                this.onEvent(JSON.parse(message.data));
            } catch (error) {
                console.error("Invalid event payload:", error);
            }
        });

        this.socket.addEventListener("close", () => {
            this.onStatus({ connected: false, transactionId });
        });

        this.socket.addEventListener("error", (error) => {
            console.error("WebSocket error:", error);
            this.onStatus({ connected: false, transactionId, error });
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