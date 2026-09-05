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

        this.governor = new GovernorVisualization(container);

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
                    `LIVE · EVENT ${event.sequence_number ?? "-"}`,
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
            <div class="transaction-console-label">
                GOVERNOR TRANSACTION CONSOLE
            </div>

            <div class="transaction-console-status">
                <span
                    id="transaction-stream-status"
                    class="transaction-stream-status"
                >
                    WAITING FOR TRANSACTION
                </span>
            </div>
        `;

        this.container.prepend(controls);

        this.status =
            controls.querySelector(
                "#transaction-stream-status",
            );
    }

    async connectToTransaction(transactionId) {
        const value =
            String(transactionId || "").trim();

        if (!value) {
            return;
        }

        this.transactionId = value;

        this.governor.reset();

        this.setStatus(
            "LOADING TRANSACTION AUDIT",
        );

        const loaded =
            await this.loadAudit(value);

        if (!loaded) {
            return;
        }

        this.setStatus(
            "LIVE EVENT STREAM",
        );

        this.eventClient.connect(value);
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

            this.governor.hydrateFromAudit(
                data,
            );

            return true;
        } catch (error) {
            console.error(
                "[Transaction Audit Error]",
                error,
            );

            this.governor.showAuditError(
                error.message ||
                "Unable to load transaction audit.",
            );

            this.setStatus(
                "AUDIT LOAD FAILED",
            );

            return false;
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

