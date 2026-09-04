import { Globe } from "./world/globe.js";
import { GlobeState } from "./world/globe-state.js";
import { EventClient } from "./world/event-client.js";
import { CommerceWorld } from "./world/commerce-world.js";
import { TransactionView } from "./world/transaction-view.js";
import { VoiceController } from "./world/voice.js";
import { VoiceCommandParser } from "./world/voice-command.js";

const container = document.getElementById("globe-container");
const statusElement = document.getElementById("network-status");
const worldOverlay = document.querySelector(".world-overlay");
const backButton = document.getElementById("world-back");
const globeState = new GlobeState();
const governorContainer = document.createElement("div");
governorContainer.id = "governor-visualization";
document.body.appendChild(governorContainer);
let globe = null;
let commerceWorld = null;

const regions = {
	asia: { id: "asia", label: "ASIA", lat: 20, lon: 100 },
	europe: { id: "europe", label: "EUROPE", lat: 50, lon: 15 },
	americas: { id: "americas", label: "AMERICAS", lat: 35, lon: -100 },
};

function showCommerceWorld(region) {
	if (globe) {
		globe.destroy();
		globe = null;
	}
	container.innerHTML = "";
	document.body.classList.add("commerce-world-active");
	worldOverlay.innerHTML = `
		<div class="eyebrow">COMMERCE TERRITORY</div>
		<h1>${region.label}</h1>
		<p>Merchant infrastructure is establishing a governed commerce environment.</p>
	`;
	commerceWorld = new CommerceWorld(container, {
        region,

        onMerchantSelected(selection) {
                console.log(
                        "[Merchant Selected]",
                        selection,
                );

                window.governorWorld.commerceSelection = {
                        merchantId: selection.merchantId,
                        itemId: selection.itemId || null,
                        regionId: selection.regionId,
                };
        },
});

function showGlobe() {
	commerceWorld?.destroy();
	commerceWorld = null;
	container.innerHTML = "";
	document.body.classList.remove("commerce-world-active");
	worldOverlay.innerHTML = `
		<div class="eyebrow">AGENTIC COMMERCE NETWORK</div>
		<h1>Commerce, at planetary scale.</h1>
		<p>A governed network for autonomous transactions.</p>
	`;
	globe = new Globe(container, {
		onNodeSelected(region) {
			const resolvedRegion = regions[region.id];
			if (resolvedRegion) showCommerceWorld(resolvedRegion);
		},
	});
}

const eventClient = new EventClient();
const voiceCommandParser = new VoiceCommandParser();
eventClient.onStatus((status) => {
	globeState.setConnected(status.connected);
	statusElement.textContent = status.connected ? "LIVE EVENT STREAM" : "NETWORK READY";
	document.body.dataset.connected = String(status.connected);
});
eventClient.onEvent((event) => {
	const action = globeState.applyEvent(event);
	console.log("[Governor Event]", action);
});

const transactionView = new TransactionView({
	container: governorContainer,
	eventClient,
	globeState,
});

const voiceContainer = document.createElement("div");
voiceContainer.id = "voice-control";
document.body.appendChild(voiceContainer);

const voiceController = new VoiceController({
	container: voiceContainer,

	onTranscript: async (transcript) => {
		console.log("[Voice Command]", transcript);

		try {
			const command = voiceCommandParser.parse(transcript);

			console.log("[Voice Intent]", command);

			window.governorWorld.voiceIntent = command;

			const commerceWorld =
				window.governorWorld.getCommerceWorld();

			const region = commerceWorld?.region;

			const merchantId =
				region?.merchantId ||
				commerceWorld?.merchantId ||
				null;

			const itemId =
				commerceWorld?.selectedItemId ||
				null;

			if (!merchantId && !itemId) {
				console.warn(
					"[Voice Commerce] No merchant/item selected yet."
				);

				return;
			}

			const response = await fetch(
				"/api/v1/voice/negotiate",
				{
					method: "POST",
					headers: {
						"Content-Type": "application/json",
					},
					body: JSON.stringify({
						merchant_id: merchantId,
						item_id: itemId,
						maximum_price: command.maximumPrice,
						currency: command.currency,
					}),
				}
			);

			const data = await response.json();

			if (!response.ok) {
				throw new Error(
					data.detail ||
					`Voice negotiation failed (${response.status})`
				);
			}

			console.log(
				"[Voice Negotiation Result]",
				data
			);

			window.governorWorld.voiceNegotiation = data;

		} catch (error) {
			console.error(
				"[Voice Commerce Error]",
				error
			);
		}
	},

	onStatus(status) {
		console.log("[Voice Status]", status);
	},
});

showGlobe();
backButton.addEventListener("click", showGlobe);

window.governorWorld = {
        globeState,
        eventClient,
        transactionView,
        voiceController,
        voiceCommandParser,
        voiceIntent: null,
        commerceSelection: null,
        voiceNegotiation: null,
        getGlobe: () => globe,
        getCommerceWorld: () => commerceWorld,
        showGlobe,
};
}

