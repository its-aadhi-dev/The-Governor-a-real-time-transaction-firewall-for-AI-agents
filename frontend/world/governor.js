export class GovernorVisualization {
    constructor(container) {
        if (!container) {
            throw new Error("Governor visualization container is required.");
        }

        this.container = container;
        this.currentState = {
            decision: null,
            riskScore: null,
            riskLevel: null,
            reason: null,
            policyVersion: null,
        };
        this.render();
    }

    render() {
        this.container.innerHTML = `
            <aside class="governor-panel">
                <div class="governor-panel-header">
                    <div>
                        <div class="governor-kicker">THE GOVERNOR</div>
                        <div class="governor-title">TRANSACTION INSPECTION</div>
                    </div>
                    <div id="governor-state" class="governor-state governor-state-idle">IDLE</div>
                </div>
                <div class="governor-rule-list">
                    ${this.rule("PRICE", "price")}
                    ${this.rule("VELOCITY", "velocity")}
                    ${this.rule("REPUTATION", "reputation")}
                    ${this.rule("COLLUSION", "collusion")}
                    ${this.rule("RISK", "risk")}
                </div>
                <div class="governor-decision">
                    <div class="governor-decision-label">DECISION</div>
                    <div id="governor-decision" class="governor-decision-value">WAITING</div>
                </div>
                <div class="governor-details">
                    <div class="governor-detail"><span>RISK SCORE</span><strong id="governor-risk-score">-</strong></div>
                    <div class="governor-detail"><span>RISK LEVEL</span><strong id="governor-risk-level">-</strong></div>
                    <div class="governor-detail"><span>POLICY</span><strong id="governor-policy">-</strong></div>
                </div>
                <div class="governor-reason">
                    <div class="governor-reason-label">GOVERNOR REASON</div>
                    <div id="governor-reason-text">Waiting for a transaction event.</div>
                </div>
            </aside>
        `;
    }

    rule(label, key) {
        return `<div class="governor-rule governor-rule-pending" data-rule="${key}"><span class="governor-rule-indicator"></span><span>${label}</span><span class="governor-rule-status" data-rule-status="${key}">WAITING</span></div>`;
    }

    consumeEvent(event) {
        if (!event?.event_type) return;
        switch (event.event_type) {
            case "GOVERNOR_EVALUATING": this.startEvaluation(); break;
            case "GOVERNOR_ALLOW": this.applyDecision("ALLOW", event); break;
            case "GOVERNOR_REVIEW": this.applyDecision("REVIEW", event); break;
            case "GOVERNOR_BLOCK": this.applyDecision("BLOCK", event); break;
            case "GOVERNOR_FALLBACK": this.applyDecision("FALLBACK", event); break;
            case "PAYMENT_PENDING": this.setState("PAYMENT PENDING"); break;
            case "PAYMENT_PAID": this.setState("PAID"); break;
            case "PAYMENT_FAILED": this.setState("PAYMENT FAILED"); break;
            default: break;
        }
    }

    startEvaluation() {
        this.setState("EVALUATING");
        for (const key of ["price", "velocity", "reputation", "collusion", "risk"]) this.updateRule(key, "EVALUATING");
        this.setDecision("EVALUATING");
    }

    applyDecision(decision, event) {
        const payload = event.payload || {};
        this.currentState = { ...this.currentState, decision, riskScore: payload.risk_score ?? null, riskLevel: payload.risk_level ?? null, reason: payload.reason ?? null, policyVersion: payload.policy_version ?? null };
        this.setState(decision);
        this.setDecision(decision);
        for (const key of ["price", "velocity", "reputation", "collusion"]) this.updateRule(key, decision);
        this.updateRule("risk", payload.risk_level ?? decision);
        this.setText("governor-risk-score", payload.risk_score ?? "-");
        this.setText("governor-risk-level", payload.risk_level ?? "-");
        this.setText("governor-policy", payload.policy_version ?? "-");
        this.setText("governor-reason-text", payload.reason ?? "Governor decision received.");
    }

    setState(state) {
        const element = this.container.querySelector("#governor-state");
        if (!element) return;
        element.textContent = state;
        element.className = `governor-state governor-state-${String(state).toLowerCase().replace(/\s+/g, "-")}`;
    }

    setDecision(decision) {
        const element = this.container.querySelector("#governor-decision");
        if (!element) return;
        element.textContent = decision;
        element.className = `governor-decision-value decision-${String(decision).toLowerCase()}`;
    }

    updateRule(key, status) {
        const row = this.container.querySelector(`[data-rule="${key}"]`);
        const label = this.container.querySelector(`[data-rule-status="${key}"]`);
        if (!row || !label) return;
        label.textContent = String(status);
        row.className = `governor-rule governor-rule-${String(status).toLowerCase().replace(/\s+/g, "-")}`;
    }

    setText(id, value) {
        const element = this.container.querySelector(`#${id}`);
        if (element) element.textContent = value;
    }

    reset() {
        this.currentState = { decision: null, riskScore: null, riskLevel: null, reason: null, policyVersion: null };
        this.setState("IDLE");
        this.setDecision("WAITING");
        for (const key of ["price", "velocity", "reputation", "collusion", "risk"]) {
            this.updateRule(key, "WAITING");
        }
        this.setText("governor-risk-score", "-");
        this.setText("governor-risk-level", "-");
        this.setText("governor-policy", "-");
        this.setText("governor-reason-text", "Waiting for a transaction event.");
    }
}
