import { Globe } from "./world/globe.js";
import { GlobeState } from "./world/globe-state.js";
import { EventClient } from "./world/event-client.js";
import { CommerceWorld } from "./world/commerce-world.js";
import { TransactionView } from "./world/transaction-view.js";
import { VoiceController } from "./world/voice.js";
import { VoiceCommandParser } from "./world/voice-command.js";
import { RazorpayCheckout } from "./world/razorpay-checkout.js";

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
        asia: {
                id: "asia",
                label: "ASIA",
                lat: 20,
                lon: 100,
        },

        europe: {
                id: "europe",
                label: "EUROPE",
                lat: 50,
                lon: 15,
        },

        americas: {
                id: "americas",
                label: "AMERICAS",
                lat: 35,
                lon: -100,
        },
};

const nodeRegions = {
        mumbai: regions.asia,
        singapore: regions.asia,
        tokyo: regions.asia,
        dubai: regions.asia,

        london: regions.europe,
        frankfurt: regions.europe,

        "new-york": regions.americas,
        "san-francisco": regions.americas,
        "sao-paulo": regions.americas,
};

async function loadVoiceMarket() {
	const response = await fetch(
		"/api/v1/voice/market",
	);

	if (!response.ok) {
		throw new Error(
			`Market request failed: ${response.status}`,
		);
	}

	const data = await response.json();

	return data.merchants || [];
}

async function showCommerceWorld(region) {
	if (globe) {
		globe.destroy();
		globe = null;
	}

	container.innerHTML = "";

	document.body.classList.add(
		"commerce-world-active",
	);

	worldOverlay.innerHTML = `
		<div class="eyebrow">
			COMMERCE TERRITORY
		</div>

		<h1>${region.label}</h1>

		<p>
			Merchant infrastructure is establishing a
			governed commerce environment.
		</p>
	`;

	try {
		const merchants =
			await loadVoiceMarket();

		commerceWorld =
			new CommerceWorld(
				container,
				{
					region,
					merchants:
						/*
						 * The database currently
						 * contains generated event
						 * fixtures. Keep the first
						 * four real records for the
						 * visual territory.
						 */
						merchants.slice(
							0,
							4,
						),

					onMerchantSelected(
						selection,
					) {
						console.log(
							"[Merchant Selected]",
							selection,
						);

						window
							.governorWorld
							.commerceSelection =
							selection;
					},
				},
			);

		console.log(
			"[Commerce Market]",
			merchants,
		);
	} catch (error) {
		console.error(
			"[Commerce Market Error]",
			error,
		);

		worldOverlay.innerHTML += `
			<p>
				MARKET DATA UNAVAILABLE
			</p>
		`;
	}
}

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
		onNodeSelected(node) {
        const resolvedRegion =
                nodeRegions[node.id];

        console.log(
                "[Network Node]",
                node.label,
                "→",
                resolvedRegion?.label,
        );

        if (resolvedRegion) {
                showCommerceWorld(
                        resolvedRegion,
                );
        }
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

			if (command.needsMaximumPrice) {
				window.governorWorld.pendingVoiceCommand =
					command;

				console.log(
					"[Voice Commerce] Maximum price required.",
				);

				window.dispatchEvent(
					new CustomEvent(
						"governor-voice-followup",
						{
							detail: {
								prompt:
									"What is your maximum price?",
								command,
							},
						},
					),
				);

				return;
			}

			const selection =
				window.governorWorld.commerceSelection;

			if (!selection?.merchantId) {
				console.warn(
					"[Voice Commerce] Select a merchant first.",
				);
				return;
			}

			const response = await fetch(
				"/api/v1/voice/negotiate",
				{
					method: "POST",

					headers: {
						"Content-Type":
							"application/json",
					},

					body: JSON.stringify({
						merchant_id:
							selection.merchantId,

						item_id:
							selection.itemId,

						maximum_price:
							command.maximumPrice,

						currency:
							command.currency,
					}),
				},
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
				data,
			);

			window.governorWorld.voiceNegotiation = data;
			await transactionView.connectToTransaction(
				data.transaction_id,
			);

			const decision = data?.governor?.decision;

			if (decision !== "ALLOW") {
				console.log(
					"[Voice Commerce] Governor decision:",
					decision,
				);

				return;
			}

			console.log(
				"[Voice Commerce] Governor ALLOW. Creating checkout order..."
			);

			const checkoutResponse = await fetch(
				`/api/v1/transactions/${encodeURIComponent(
					data.transaction_id,
				)}/checkout`,
				{
					method: "POST",
				},
			);

			const checkoutData = await checkoutResponse.json();

			if (!checkoutResponse.ok) {
				throw new Error(
					checkoutData.detail ||
					`Checkout creation failed (${checkoutResponse.status}).`,
				);
			}

			console.log(
				"[Voice Checkout Order]",
				checkoutData,
			);

			await razorpayCheckout.open({
				keyId: checkoutData.key_id,
				orderId: checkoutData.order_id,
				amount: checkoutData.amount,
				currency: checkoutData.currency,
				itemName: data.item?.item_name,
				transactionId: data.transaction_id,
			});

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

const razorpayCheckout = new RazorpayCheckout();

window.addEventListener(
	"governor-payment-verified",
	(event) => {
		console.log(
			"[Governor] PAYMENT VERIFIED",
			event.detail,
		);
	},
);

window.addEventListener(
	"governor-payment-verification-failed",
	(event) => {
		console.error(
			"[Governor] PAYMENT VERIFICATION FAILED",
			event.detail,
		);
	},
);

window.addEventListener(
	"governor-voice-followup",
	(event) => {
		console.log(
			"[Governor Voice Follow-up]",
			event.detail.prompt,
		);
	},
);



showGlobe();
backButton.addEventListener("click", showGlobe);

window.governorWorld = {
	globeState,
	eventClient,
	transactionView,
	voiceController,
	voiceCommandParser,
	razorpayCheckout,
	voiceIntent: null,
	commerceSelection: null,
	voiceNegotiation: null,
	getGlobe: () => globe,
	getCommerceWorld: () => commerceWorld,
	showGlobe,
};
