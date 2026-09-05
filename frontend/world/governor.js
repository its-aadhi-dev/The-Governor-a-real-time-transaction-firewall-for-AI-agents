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
                            TRANSACTION INSPECTION
                        </div>
                    </div>

                    <div
                        id="governor-state"
                        class="governor-state governor-state-idle"
                    >
                        IDLE
                    </div>
                </div>

                <!-- TRANSACTION LIFECYCLE -->

                <div class="governor-audit">
                    <div class="governor-audit-header">
                        <span>TRANSACTION LIFECYCLE</span>
                        <span id="governor-ledger-status">
                            WAITING
                        </span>
                    </div>

                    <div
                        id="governor-audit-events"
                        class="governor-audit-events"
                    >
                        <div class="governor-audit-empty">
                            Waiting for transaction events.
                        </div>
                    </div>
                </div>

                <!-- GOVERNOR RULES -->

                <div class="governor-rule-list">
                    ${this.rule("PRICE", "price")}
                    ${this.rule("VELOCITY", "velocity")}
                    ${this.rule("REPUTATION", "reputation")}
                    ${this.rule("COLLUSION", "collusion")}
                    ${this.rule("RISK", "risk")}
                </div>

                <!-- DECISION -->

                <div class="governor-decision">
                    <div class="governor-decision-label">
                        DECISION
                    </div>

                    <div
                        id="governor-decision"
                        class="governor-decision-value"
                    >
                        WAITING
                    </div>
                </div>

                <div class="governor-details">
                    <div class="governor-detail">
                        <span>RISK SCORE</span>
                        <strong id="governor-risk-score">-</strong>
                    </div>

                    <div class="governor-detail">
                        <span>RISK LEVEL</span>
                        <strong id="governor-risk-level">-</strong>
                    </div>

                    <div class="governor-detail">
                        <span>POLICY</span>
                        <strong id="governor-policy">-</strong>
                    </div>
                </div>

                <div class="governor-reason">
                    <div class="governor-reason-label">
                        GOVERNOR REASON
                    </div>

                    <div id="governor-reason-text">
                        Waiting for a transaction event.
                    </div>
                </div>

                <!-- CRYPTOGRAPHIC AUDIT -->

                <div class="governor-audit">
                    <div class="governor-audit-header">
                        <span>CRYPTOGRAPHIC AUDIT</span>
                        <span id="governor-chain-status">
                            UNCHECKED
                        </span>
                    </div>

                    <div
                        id="governor-ledger-events"
                        class="governor-audit-events"
                    >
                        <div class="governor-audit-empty">
                            No ledger blocks loaded.
                        </div>
                    </div>
                </div>

            </aside>
        `;
    }

    rule(label, key) {
        return `
            <div
                class="governor-rule governor-rule-pending"
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

        this.appendAuditEvent(event);

        switch (event.event_type) {
            case "TRANSACTION_CREATED":
                this.setState("TRANSACTION CREATED");
                break;

            case "NEGOTIATION_STARTED":
                this.setState("NEGOTIATING");
                break;

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
                this.applyDecision("ALLOW", event);
                break;

            case "GOVERNOR_REVIEW":
                this.applyDecision("REVIEW", event);
                break;

            case "GOVERNOR_BLOCK":
                this.applyDecision("BLOCK", event);
                break;

            case "GOVERNOR_FALLBACK":
                this.applyDecision("FALLBACK", event);
                break;

            case "PAYMENT_PENDING":
                this.setState("PAYMENT PENDING");
                break;

            case "PAYMENT_VERIFIED":
                this.setState("PAYMENT VERIFIED");
                break;

            case "PAYMENT_VERIFICATION_FAILED":
                this.setState("PAYMENT VERIFY FAILED");
                break;

            case "PAYMENT_PAID":
                this.setState("PAID");
                break;

            case "PAYMENT_FAILED":
                this.setState("PAYMENT FAILED");
                break;

            default:
                break;
        }
    }

    appendAuditEvent(event) {
        this.auditEvents.push(event);

        const container =
            this.container.querySelector(
                "#governor-audit-events",
            );

        if (!container) {
            return;
        }

        if (this.auditEvents.length === 1) {
            container.innerHTML = "";
        }

        const entry = document.createElement("div");

        entry.className =
            "governor-audit-entry";

        entry.innerHTML = `
            <span class="governor-audit-sequence">
                ${event.sequence_number ?? "-"}
            </span>

            <span class="governor-audit-event">
                ${this.escapeHtml(event.event_type)}
            </span>
        `;

        container.appendChild(entry);

        container.scrollTop =
            container.scrollHeight;
    }

    startEvaluation() {
        this.setState("EVALUATING");

        for (
            const key of [
                "price",
                "velocity",
                "reputation",
                "collusion",
                "risk",
            ]
        ) {
            this.updateRule(
                key,
                "EVALUATING",
            );
        }

        this.setDecision("EVALUATING");
    }

    applyDecision(decision, event) {
        const payload =
            event.payload || {};

        this.currentState = {
            ...this.currentState,
            decision,
            riskScore:
                payload.risk_score ??
                null,
            riskLevel:
                payload.risk_level ??
                null,
            reason:
                payload.reason ??
                null,
            policyVersion:
                payload.policy_version ??
                null,
        };

        this.setState(decision);
        this.setDecision(decision);

        for (
            const key of [
                "price",
                "velocity",
                "reputation",
                "collusion",
            ]
        ) {
            this.updateRule(
                key,
                decision,
            );
        }

        this.updateRule(
            "risk",
            payload.risk_level ??
            decision,
        );

        this.setText(
            "governor-risk-score",
            payload.risk_score ??
            "-",
        );

        this.setText(
            "governor-risk-level",
            payload.risk_level ??
            "-",
        );

        this.setText(
            "governor-policy",
            payload.policy_version ??
            "-",
        );

        this.setText(
            "governor-reason-text",
            payload.reason ??
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

    loadAudit(audit) {
        const events =
            audit?.events || [];

        const ledger =
            audit?.ledger || [];

        this.auditEvents = [];

        const eventContainer =
            this.container.querySelector(
                "#governor-audit-events",
            );

        if (eventContainer) {
            eventContainer.innerHTML = "";

            if (!events.length) {
                eventContainer.innerHTML = `
                    <div class="governor-audit-empty">
                        No transaction events.
                    </div>
                `;
            } else {
                for (const event of events) {
                    this.appendAuditEntry(
                        eventContainer,
                        event.sequence_number,
                        event.event_type,
                    );
                }
            }
        }

        this.renderLedger(
            ledger,
            audit?.ledger_integrity,
        );
    }

    appendAuditEntry(
        container,
        sequence,
        eventType,
    ) {
        const entry =
            document.createElement("div");

        entry.className =
            "governor-audit-entry";

        entry.innerHTML = `
            <span class="governor-audit-sequence">
                ${sequence ?? "-"}
            </span>

            <span class="governor-audit-event">
                ${this.escapeHtml(eventType)}
            </span>
        `;

        container.appendChild(
            entry,
        );
    }

    renderLedger(
        blocks,
        integrity,
    ) {
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

        if (!blocks.length) {
            container.innerHTML = `
                <div class="governor-audit-empty">
                    No signed ledger blocks.
                </div>
            `;
        } else {
            for (const block of blocks) {
                this.appendLedgerEntry(
                    container,
                    block,
                );
            }
        }

        if (status) {
            status.textContent =
                integrity
                    ? "CHAIN VALID"
                    : "CHAIN INVALID";

            status.className =
                integrity
                    ? "governor-chain-valid"
                    : "governor-chain-invalid";
        }
    }

    appendLedgerEntry(
        container,
        block,
    ) {
        const entry =
            document.createElement("div");

        entry.className =
            "governor-audit-entry";

        entry.innerHTML = `
            <span class="governor-audit-sequence">
                ${block.sequence_number}
            </span>

            <span class="governor-audit-event">
                ${this.escapeHtml(
            block.event_type,
        )}
                ${block.valid ? " ✓" : " ✕"}
            </span>
        `;

        container.appendChild(
            entry,
        );
    }

    showAuditError(message) {
        const eventContainer =
            this.container.querySelector(
                "#governor-audit-events",
            );

        if (eventContainer) {
            eventContainer.innerHTML = `
                <div class="governor-audit-empty">
                    AUDIT ERROR
                    <br>
                    ${this.escapeHtml(message)}
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

        this.setState("IDLE");
        this.setDecision("WAITING");

        for (
            const key of [
                "price",
                "velocity",
                "reputation",
                "collusion",
                "risk",
            ]
        ) {
            this.updateRule(
                key,
                "WAITING",
            );
        }

        this.setText(
            "governor-risk-score",
            "-",
        );

        this.setText(
            "governor-risk-level",
            "-",
        );

        this.setText(
            "governor-policy",
            "-",
        );

        this.setText(
            "governor-reason-text",
            "Waiting for a transaction event.",
        );

        const events =
            this.container.querySelector(
                "#governor-audit-events",
            );

        if (events) {
            events.innerHTML = `
                <div class="governor-audit-empty">
                    Waiting for transaction events.
                </div>
            `;
        }

        const ledger =
            this.container.querySelector(
                "#governor-ledger-events",
            );

        if (ledger) {
            ledger.innerHTML = `
                <div class="governor-audit-empty">
                    No ledger blocks loaded.
                </div>
            `;
        }

        this.setText(
            "governor-chain-status",
            "UNCHECKED",
        );
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


