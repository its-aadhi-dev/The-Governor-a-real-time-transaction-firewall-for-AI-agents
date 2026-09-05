export class VoiceController {
    constructor({
        container,
        onTranscript = () => { },
        onStatus = () => { },
    }) {
        this.container = container;
        this.onTranscript = onTranscript;
        this.onStatus = onStatus;

        this.recognition = null;
        this.listening = false;

        this.render();
        this.setupRecognition();
    }

    setupRecognition() {
        const SpeechRecognition =
            window.SpeechRecognition ||
            window.webkitSpeechRecognition;

        if (!SpeechRecognition) {
            this.onStatus({
                available: false,
                listening: false,
                message: "VOICE INPUT UNAVAILABLE",
            });
            this.updateStatus("VOICE INPUT UNAVAILABLE");
            this.button.disabled = true;
            return;
        }

        this.recognition = new SpeechRecognition();

        this.recognition.continuous = false;
        this.recognition.interimResults = false;
        this.recognition.lang = "en-US";
        this.recognition.maxAlternatives = 1;

        this.recognition.onstart = () => {
            this.listening = true;
            this.updateStatus("LISTENING...");
            this.button.classList.add("is-listening");

            this.onStatus({
                available: true,
                listening: true,
                message: "LISTENING",
            });
        };

        this.recognition.onresult = (event) => {
            const result = event.results?.[0]?.[0];
            const transcript = result?.transcript?.trim();

            if (!transcript) {
                return;
            }

            this.transcriptElement.textContent = transcript;
            this.updateStatus("COMMAND RECEIVED");

            this.onTranscript(transcript);
        };

        this.recognition.onerror = (event) => {
            console.error("[Voice]", {
                error: event.error,
                message: event.message,
                type: event.type,
            });

            const messages = {
                "not-allowed": "MICROPHONE PERMISSION DENIED",
                "no-speech": "NO SPEECH DETECTED",
                "audio-capture": "MICROPHONE UNAVAILABLE",
                "network": "SPEECH SERVICE UNAVAILABLE",
                "aborted": "VOICE INPUT ABORTED",
                "language-not-supported":
                    "LANGUAGE NOT SUPPORTED",
            };

            this.updateStatus(
                messages[event.error] ||
                "VOICE INPUT ERROR",
            );
        };

        this.recognition.onend = () => {
            this.listening = false;
            this.button.classList.remove("is-listening");

            if (this.statusElement.textContent === "LISTENING...") {
                this.updateStatus("VOICE READY");
            }

            this.onStatus({
                available: true,
                listening: false,
                message: "READY",
            });
        };
    }

    start() {
        if (!this.recognition || this.listening) {
            return;
        }

        this.transcriptElement.textContent = "";
        this.updateStatus("STARTING...");

        try {
            this.recognition.start();
        } catch (error) {
            console.error("[Voice] Failed to start:", error);
            this.updateStatus("VOICE START FAILED");
        }
    }

    stop() {
        if (!this.recognition || !this.listening) {
            return;
        }

        this.recognition.stop();
    }

    toggle() {
        if (this.listening) {
            this.stop();
        } else {
            this.start();
        }
    }

    updateStatus(message) {
        this.statusElement.textContent = message;
    }

    render() {
        this.container.innerHTML = `
            <div class="voice-panel">
                <div class="voice-header">
                    <div>
                        <div class="voice-eyebrow">VOICE CONTROL</div>
                        <div class="voice-title">COMMAND THE MARKET</div>
                    </div>

                    <div class="voice-status" id="voice-status">
                        VOICE READY
                    </div>
                </div>

                <button
                    class="voice-button"
                    type="button"
                    aria-label="Start voice command"
                >
                    <span class="voice-button-icon">●</span>
                    <span class="voice-button-label">
                        SPEAK
                    </span>
                </button>

                <div class="voice-transcript-label">
                    RECOGNIZED COMMAND
                </div>

                <div class="voice-transcript">
                    <span>Waiting for a voice command...</span>
                </div>
            </div>
        `;

        this.button = this.container.querySelector(".voice-button");
        this.statusElement = this.container.querySelector(".voice-status");
        this.transcriptElement =
            this.container.querySelector(".voice-transcript span");

        this.button.addEventListener("click", () => {
            this.toggle();
        });
    }

    destroy() {
        this.stop();

        this.button?.replaceWith(this.button.cloneNode(true));
        this.container.innerHTML = "";
        this.recognition = null;
    }
}
