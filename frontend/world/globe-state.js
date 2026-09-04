export class GlobeState {
    constructor() {
        this.nodes = new Map();
        this.transactions = new Map();
        this.connected = false;
    }

    setConnected(value) {
        this.connected = Boolean(value);
    }

    applyEvent(event) {
        if (!event || !event.event_type) {
            return;
        }

        const transactionId = event.transaction_id;

        if (!transactionId) {
            return;
        }

        this.transactions.set(transactionId, {
            ...this.transactions.get(transactionId),
            ...event,
        });

        return {
            type: event.event_type,
            transactionId,
            event,
        };
    }

    addNode(node) {
        if (!node?.id) {
            throw new Error("Globe node requires an id.");
        }

        this.nodes.set(node.id, { ...node });
    }

    getNode(id) {
        return this.nodes.get(id);
    }

    getSnapshot() {
        return {
            connected: this.connected,
            nodes: [...this.nodes.values()],
            transactions: [...this.transactions.values()],
        };
    }
}