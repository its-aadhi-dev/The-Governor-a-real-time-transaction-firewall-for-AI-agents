export class GovernorVisualization {
    constructor(container) {
        if (!container) {
            throw new Error(
                "Governor visualization container is required.",
            );
        }

        this.container = container;

        this.currentState = {
            decision: null,
            riskScore: null,
            riskLevel: null,
            reason: null,
            policyVersion: null,
        };

        this.auditEvents = [];
        this.auditLedger = [];
        this.auditTransaction = null;
        this.auditNegotiation = null;

        this.render();
    }

    render() {
        this.container.innerHTML = `
            <aside class="governor-panel">

                <div class="governor-panel-header">
                    <div>
                        <div class="governor-kicker">
                            THE GOVERNOR
                        </div>
                        <div class="governor-title">
                            TRANSACTION CONSOLE
                        </div>
                    </div>

                    <div
                        id="governor-state"
                        class="governor-state governor-state-idle"
                    >
                        IDLE
                    </div>
                </div>

                <section class="governor-section">
                    <div class="governor-section-title">
                        TRANSACTION
                    </div>

                    <div class="governor-transaction-id" id="governor-transaction-id">
                        WAITING
                    </div>

                    <div class="governor-transaction-grid">
                        <div>
                            <span>STATUS</span>
                            <strong id="governor-tx-status">-</strong>
                        </div>
                        <div>
                            <span>PRICE</span>
                            <strong id="governor-tx-price">-</strong>
                        </div>
                        <div>
                            <span>AUTHORIZED</span>
                            <strong id="governor-tx-authorized">-</strong>
                        </div>
                        <div>
                            <span>CURRENCY</span>
                            <strong id="governor-tx-currency">-</strong>
                        </div>
                    </div>
                </section>

                <section class="governor-section">
                    <div class="governor-section-title">
                        NEGOTIATION
                    </div>

                    <div id="governor-negotiation-meta" class="governor-meta">
                        Waiting for negotiation.
                    </div>

                    <div
                        id="governor-negotiation"
                        class="governor-negotiation"
                    >
                        <div class="governor-empty">
                            No negotiation messages.
                        </div>
                    </div>
                </section>

                <section class="governor-section">
                    <div class="governor-section-title">
                        GOVERNANCE
                    </div>

                    <div class="governor-rule-list">
                        ${this.rule("PRICE", "price")}
                        ${this.rule("VELOCITY", "velocity")}
                        ${this.rule("REPUTATION", "reputation")}
                        ${this.rule("COLLUSION", "collusion")}
                        ${this.rule("RISK", "risk")}
                    </div>
                </section>

                <section class="governor-decision">
                    <div class="governor-section-title">
                        GOVERNOR DECISION
                    </div>

                    <div
                        id="governor-decision"
                        class="governor-decision-value decision-waiting"
                    >
                        WAITING
                    </div>

                    <div
                        id="governor-reason-text"
                        class="governor-reason-text"
                    >
                        Waiting for Governor evaluation.
                    </div>

                    <div class="governor-details">
                        <div>
                            <span>RISK SCORE</span>
                            <strong id="governor-risk-score">-</strong>
                        </div>

                        <div>
                            <span>RISK LEVEL</span>
                            <strong id="governor-risk-level">-</strong>
                        </div>

                        <div>
                            <span>POLICY</span>
                            <strong id="governor-policy">-</strong>
                        </div>
                    </div>
                </section>

                <section class="governor-section">
                    <div class="governor-section-title">
                        PAYMENT
                    </div>

                    <div class="governor-payment-grid">
                        <div>
                            <span>RAZORPAY ORDER</span>
                            <strong id="governor-order-id">-</strong>
                        </div>

                        <div>
                            <span>PAYMENT STATUS</span>
                            <strong id="governor-payment-status">
                                NOT STARTED
                            </strong>
                        </div>
                    </div>
                </section>

                <section class="governor-section">
                    <div class="governor-section-title">
                        EVENT STREAM
                    </div>

                    <div
                        id="governor-audit-events"
                        class="governor-audit-events"
                    >
                        <div class="governor-empty">
                            Waiting for events.
                        </div>
                    </div>
                </section>

                <section class="governor-section">
                    <div class="governor-section-title">
                        CRYPTOGRAPHIC AUDIT
                        <span
                            id="governor-chain-status"
                            class="governor-chain-status"
                        >
                            UNCHECKED
                        </span>
                    </div>

                    <div
                        id="governor-ledger-events"
                        class="governor-audit-events"
                    >
                        <div class="governor-empty">
                            No ledger blocks loaded.
                        </div>
                    </div>
                </section>

            </aside>
        `;
    }

    rule(label, key) {
        return `
            <div
                class="governor-rule governor-rule-waiting"
                data-rule="${key}"
            >
                <span class="governor-rule-indicator"></span>
                <span>${label}</span>
                <span
                    class="governor-rule-status"
                    data-rule-status="${key}"
                >
                    WAITING
                </span>
            </div>
        `;
    }

    consumeEvent(event) {
        if (!event?.event_type) {
            return;
        }

        this.upsertAuditEvent(event);

        const payload = event.payload || {};

        switch (event.event_type) {
            case "TRANSACTION_CREATED":
                this.setState("TRANSACTION CREATED");
                break;

            case "NEGOTIATION_STARTED":
            case "OFFER_CREATED":
            case "COUNTER_OFFER":
                this.setState("NEGOTIATING");
                break;

            case "DEAL_ACCEPTED":
                this.setState("DEAL ACCEPTED");
                break;

            case "GOVERNOR_EVALUATING":
                this.startEvaluation();
                break;

            case "GOVERNOR_ALLOW":
                this.applyDecision("ALLOW", payload);
                break;

            case "GOVERNOR_REVIEW":
                this.applyDecision("REVIEW", payload);
                break;

            case "GOVERNOR_BLOCK":
                this.applyDecision("BLOCK", payload);
                break;

            case "GOVERNOR_FALLBACK":
                this.applyDecision("FALLBACK", payload);
                break;

            case "PAYMENT_PENDING":
                this.setState("PAYMENT PENDING");
                this.setText(
                    "governor-payment-status",
                    "PAYMENT PENDING",
                );
                break;

            case "PAYMENT_VERIFIED":
                this.setState("PAYMENT VERIFIED");
                this.setText(
                    "governor-payment-status",
                    "PAYMENT VERIFIED",
                );
                break;

            case "PAYMENT_VERIFICATION_FAILED":
                this.setState("PAYMENT VERIFY FAILED");
                this.setText(
                    "governor-payment-status",
                    "VERIFICATION FAILED",
                );
                break;

            case "PAYMENT_PAID":
                this.setState("PAID");
                this.setText(
                    "governor-payment-status",
                    "PAID",
                );
                break;

            case "PAYMENT_FAILED":
                this.setState("PAYMENT FAILED");
                this.setText(
                    "governor-payment-status",
                    "PAYMENT FAILED",
                );
                break;

            default:
                break;
        }

        if (payload.order_id) {
            this.setText(
                "governor-order-id",
                payload.order_id,
            );
        }
    }

    hydrateFromAudit(audit) {
        this.reset();

        this.auditTransaction =
            audit?.transaction || null;

        this.auditNegotiation =
            audit?.negotiation || null;

        this.auditEvents =
            [...(audit?.events || [])];

        this.auditLedger =
            [...(audit?.ledger || [])];

        this.renderTransaction(audit);
        this.renderNegotiation(audit);
        this.renderEvents();
        this.renderLedger();

        const transaction =
            audit?.transaction || {};

        if (transaction.decision) {
            this.applyDecision(
                transaction.decision,
                this.findDecisionPayload(
                    audit?.events || [],
                ),
            );
        }

        if (transaction.status) {
            this.setState(
                this.humanState(transaction.status),
            );
        }

        if (transaction.razorpay_order_id) {
            this.setText(
                "governor-order-id",
                transaction.razorpay_order_id,
            );
        }

        this.updatePaymentStatus(
            transaction.status,
            audit?.events || [],
        );
    }

    renderTransaction(audit) {
        const tx =
            audit?.transaction || {};

        this.setText(
            "governor-transaction-id",
            audit?.transaction_id || "-",
        );

        this.setText(
            "governor-tx-status",
            tx.status || "-",
        );

        this.setText(
            "governor-tx-price",
            tx.requested_price
                ? `₹${tx.requested_price}`
                : "-",
        );

        this.setText(
            "governor-tx-authorized",
            tx.authorized_price
                ? `₹${tx.authorized_price}`
                : "-",
        );

        this.setText(
            "governor-tx-currency",
            tx.currency || "-",
        );
    }

    renderNegotiation(audit) {
        const negotiation =
            audit?.negotiation;

        const meta =
            this.container.querySelector(
                "#governor-negotiation-meta",
            );

        const container =
            this.container.querySelector(
                "#governor-negotiation",
            );

        if (!container) {
            return;
        }

        const messages =
            negotiation?.messages || [];

        if (meta) {
            meta.textContent =
                negotiation
                    ? `${negotiation.status || "UNKNOWN"} · ${negotiation.proposal_count ?? 0
                    } PROPOSALS`
                    : "No negotiation record.";
        }

        if (!messages.length) {
            container.innerHTML = `
                <div class="governor-empty">
                    No negotiation messages.
                </div>
            `;
            return;
        }

        container.innerHTML = "";

        for (const message of messages) {
            const entry =
                document.createElement("div");

            entry.className =
                "governor-negotiation-message";

            const role =
                String(message.agent_id || "")
                    .includes("buyer")
                    ? "BUYER"
                    : "MERCHANT";

            entry.innerHTML = `
                <div class="governor-message-head">
                    <span>${role}</span>
                    <span>#${message.sequence_number ?? "-"
                }</span>
                </div>

                <div class="governor-message-body">
                    ${this.escapeHtml(
                    message.message || "",
                )}
                </div>

                ${message.proposed_price
                    ? `
                            <div class="governor-message-price">
                                ₹${this.escapeHtml(
                        message.proposed_price,
                    )}
                            </div>
                        `
                    : ""
                }
            `;

            container.appendChild(entry);
        }
    }

    renderEvents() {
        const container =
            this.container.querySelector(
                "#governor-audit-events",
            );

        if (!container) {
            return;
        }

        container.innerHTML = "";

        if (!this.auditEvents.length) {
            container.innerHTML = `
                <div class="governor-empty">
                    No transaction events.
                </div>
            `;
            return;
        }

        for (const event of this.auditEvents) {
            this.appendAuditEntry(
                container,
                event,
            );
        }
    }

    renderLedger() {
        const container =
            this.container.querySelector(
                "#governor-ledger-events",
            );

        const status =
            this.container.querySelector(
                "#governor-chain-status",
            );

        if (!container) {
            return;
        }

        container.innerHTML = "";

        if (!this.auditLedger.length) {
            container.innerHTML = `
                <div class="governor-empty">
                    No signed ledger blocks.
                </div>
            `;
        } else {
            for (const block of this.auditLedger) {
                this.appendLedgerEntry(
                    container,
                    block,
                );
            }
        }

        if (status) {
            const valid =
                this.auditLedger.length > 0;

            status.textContent =
                valid
                    ? "CHAIN VALID"
                    : "UNCHECKED";

            status.className =
                valid
                    ? "governor-chain-status governor-chain-valid"
                    : "governor-chain-status";
        }
    }

    upsertAuditEvent(event) {
        const existingIndex =
            this.auditEvents.findIndex(
                (item) =>
                    item.event_id === event.event_id,
            );

        if (existingIndex >= 0) {
            return;
        }

        this.auditEvents.push(event);
        this.auditEvents.sort(
            (a, b) =>
                (a.sequence_number ?? 0) -
                (b.sequence_number ?? 0),
        );

        this.renderEvents();
    }

    appendAuditEntry(container, event) {
        const entry =
            document.createElement("div");

        entry.className =
            "governor-audit-entry";

        entry.innerHTML = `
            <span class="governor-audit-sequence">
                ${event.sequence_number ?? "-"}
            </span>

            <span class="governor-audit-event">
                ${this.escapeHtml(
            event.event_type,
        )}
            </span>
        `;

        container.appendChild(entry);
    }

    appendLedgerEntry(container, block) {
        const entry =
            document.createElement("div");

        entry.className =
            "governor-audit-entry";

        entry.innerHTML = `
            <span class="governor-audit-sequence">
                ${block.sequence_number ?? "-"}
            </span>

            <span class="governor-audit-event">
                ${this.escapeHtml(
            block.event_type || "",
        )}
                ${block.valid ? "✓" : "✕"}
            </span>
        `;

        container.appendChild(entry);
    }

    startEvaluation() {
        this.setState("EVALUATING");
        this.setDecision("EVALUATING");

        for (const key of [
            "price",
            "velocity",
            "reputation",
            "collusion",
            "risk",
        ]) {
            this.updateRule(
                key,
                "EVALUATING",
            );
        }
    }

    applyDecision(decision, payload = {}) {
        this.currentState = {
            ...this.currentState,
            decision,
            riskScore:
                payload.risk_score ??
                this.currentState.riskScore,
            riskLevel:
                payload.risk_level ??
                this.currentState.riskLevel,
            reason:
                payload.reason ??
                this.currentState.reason,
            policyVersion:
                payload.policy_version ??
                this.currentState.policyVersion,
        };

        this.setState(decision);
        this.setDecision(decision);

        for (const key of [
            "price",
            "velocity",
            "reputation",
            "collusion",
        ]) {
            this.updateRule(
                key,
                decision,
            );
        }

        this.updateRule(
            "risk",
            payload.risk_level ||
            this.currentState.riskLevel ||
            decision,
        );

        this.setText(
            "governor-risk-score",
            this.currentState.riskScore ?? "-",
        );

        this.setText(
            "governor-risk-level",
            this.currentState.riskLevel ?? "-",
        );

        this.setText(
            "governor-policy",
            this.currentState.policyVersion ?? "-",
        );

        this.setText(
            "governor-reason-text",
            this.currentState.reason ||
            "Governor decision received.",
        );
    }

    setState(state) {
        const element =
            this.container.querySelector(
                "#governor-state",
            );

        if (!element) {
            return;
        }

        element.textContent = state;

        element.className =
            `governor-state governor-state-${String(
                state,
            )
                .toLowerCase()
                .replace(/\s+/g, "-")}`;
    }

    setDecision(decision) {
        const element =
            this.container.querySelector(
                "#governor-decision",
            );

        if (!element) {
            return;
        }

        element.textContent =
            decision;

        element.className =
            `governor-decision-value decision-${String(
                decision,
            ).toLowerCase()}`;
    }

    updateRule(key, status) {
        const row =
            this.container.querySelector(
                `[data-rule="${key}"]`,
            );

        const label =
            this.container.querySelector(
                `[data-rule-status="${key}"]`,
            );

        if (!row || !label) {
            return;
        }

        label.textContent =
            String(status);

        row.className =
            `governor-rule governor-rule-${String(
                status,
            )
                .toLowerCase()
                .replace(/\s+/g, "-")}`;
    }

    updatePaymentStatus(status, events) {
        const paymentEvent =
            [...events]
                .reverse()
                .find((event) =>
                    String(event.event_type)
                        .startsWith("PAYMENT_"),
                );

        if (paymentEvent) {
            const map = {
                PAYMENT_PENDING:
                    "PAYMENT PENDING",
                PAYMENT_VERIFIED:
                    "PAYMENT VERIFIED",
                PAYMENT_VERIFICATION_FAILED:
                    "VERIFICATION FAILED",
                PAYMENT_PAID:
                    "PAID",
                PAYMENT_FAILED:
                    "PAYMENT FAILED",
            };

            this.setText(
                "governor-payment-status",
                map[paymentEvent.event_type] ||
                paymentEvent.event_type,
            );

            return;
        }

        if (status) {
            this.setText(
                "governor-payment-status",
                status === "APPROVED"
                    ? "READY"
                    : "NOT STARTED",
            );
        }
    }

    findDecisionPayload(events) {
        const event =
            [...events]
                .reverse()
                .find((item) =>
                    [
                        "GOVERNOR_ALLOW",
                        "GOVERNOR_REVIEW",
                        "GOVERNOR_BLOCK",
                        "GOVERNOR_FALLBACK",
                    ].includes(
                        item.event_type,
                    ),
                );

        return event?.payload || {};
    }

    humanState(status) {
        const map = {
            CREATED:
                "TRANSACTION CREATED",
            GOVERNANCE_PENDING:
                "GOVERNANCE PENDING",
            APPROVED:
                "APPROVED",
            REVIEW:
                "REVIEW",
            BLOCKED:
                "BLOCKED",
            FALLBACK:
                "FALLBACK",
            PAYMENT_PENDING:
                "PAYMENT PENDING",
            PAID:
                "PAID",
            FAILED:
                "FAILED",
        };

        return map[status] || status;
    }

    setText(id, value) {
        const element =
            this.container.querySelector(
                `#${id}`,
            );

        if (element) {
            element.textContent =
                value;
        }
    }

    showAuditError(message) {
        this.setState("AUDIT ERROR");

        const container =
            this.container.querySelector(
                "#governor-audit-events",
            );

        if (container) {
            container.innerHTML = `
                <div class="governor-empty">
                    AUDIT ERROR
                    <br>
                    ${this.escapeHtml(
                message,
            )}
                </div>
            `;
        }
    }

    reset() {
        this.currentState = {
            decision: null,
            riskScore: null,
            riskLevel: null,
            reason: null,
            policyVersion: null,
        };

        this.auditEvents = [];
        this.auditLedger = [];
        this.auditTransaction = null;
        this.auditNegotiation = null;

        this.render();

        this.setState("IDLE");
        this.setDecision("WAITING");
    }

    escapeHtml(value) {
        return String(value)
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    }
}

