import { GovernorVisualization } from "./governor.js";

export class TransactionView {
    constructor({ container, eventClient, globeState }) {
        if (!container) {
            throw new Error(
                "Transaction view container is required.",
            );
        }

        this.container = container;
        this.eventClient = eventClient;
        this.globeState = globeState;
        this.transactionId = null;

        this.governor =
            new GovernorVisualization(container);

        this.renderControls();

        this.removeEventListener =
            this.eventClient.onEvent((event) => {
                if (
                    event.transaction_id !==
                    this.transactionId
                ) {
                    return;
                }

                this.globeState.applyEvent(event);
                this.governor.consumeEvent(event);

                this.setStatus(
                    `LIVE - EVENT ${event.sequence_number}`,
                );
            });

        this.removeStatusListener =
            this.eventClient.onStatus((status) => {
                if (
                    status.transactionId !==
                    this.transactionId
                ) {
                    return;
                }

                this.setStatus(
                    status.connected
                        ? "LIVE EVENT STREAM"
                        : "EVENT STREAM DISCONNECTED",
                );
            });
    }

    renderControls() {
        const controls =
            document.createElement("div");

        controls.className =
            "transaction-connect";

        controls.innerHTML = `
            <div class="transaction-connect-label">
                LIVE TRANSACTION
            </div>

            <div class="transaction-connect-row">
                <input
                    id="transaction-id-input"
                    type="text"
                    placeholder="Transaction ID"
                    autocomplete="off"
                >

                <button
                    id="transaction-connect-button"
                    type="button"
                >
                    CONNECT
                </button>
            </div>

            <div
                id="transaction-stream-status"
                class="transaction-stream-status"
            >
                EVENT STREAM OFFLINE
            </div>
        `;

        this.container.prepend(
            controls,
        );

        this.input =
            controls.querySelector(
                "#transaction-id-input",
            );

        this.button =
            controls.querySelector(
                "#transaction-connect-button",
            );

        this.status =
            controls.querySelector(
                "#transaction-stream-status",
            );

        this.button.addEventListener(
            "click",
            () => this.connect(),
        );
    }

    async connectToTransaction(
        transactionId,
    ) {
        const value =
            String(transactionId || "").trim();

        if (!value) {
            return;
        }

        this.input.value = value;

        await this.connect();
    }

    async connect() {
        const transactionId =
            this.input.value.trim();

        if (!transactionId) {
            this.setStatus(
                "TRANSACTION ID REQUIRED",
            );

            return;
        }

        this.transactionId =
            transactionId;

        this.governor.reset();

        this.setStatus(
            "LOADING TRANSACTION AUDIT",
        );

        await this.loadAudit(
            transactionId,
        );

        this.setStatus(
            "CONNECTING TO EVENT STREAM",
        );

        this.eventClient.connect(
            transactionId,
        );
    }

    async loadAudit(transactionId) {
        try {
            const response =
                await fetch(
                    `/api/v1/transactions/${encodeURIComponent(
                        transactionId,
                    )}/audit`,
                );

            const data =
                await response.json();

            if (!response.ok) {
                throw new Error(
                    data.detail ||
                    `Audit request failed (${response.status}).`,
                );
            }

            console.log(
                "[Transaction Audit]",
                data,
            );

            this.governor.loadAudit(
                data,
            );
        } catch (error) {
            console.error(
                "[Transaction Audit Error]",
                error,
            );

            this.governor.showAuditError(
                error.message,
            );
        }
    }

    setStatus(value) {
        if (this.status) {
            this.status.textContent =
                value;
        }
    }

    destroy() {
        this.removeEventListener?.();
        this.removeStatusListener?.();
        this.eventClient.disconnect();
        this.container.innerHTML = "";
    }
}

