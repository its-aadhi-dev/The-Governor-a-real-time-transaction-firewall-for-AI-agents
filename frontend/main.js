import { Globe } from "./world/globe.js";
import { GlobeState } from "./world/globe-state.js";
import { EventClient } from "./world/event-client.js";
import { CommerceWorld } from "./world/commerce-world.js";

const container = document.getElementById("globe-container");
const statusElement = document.getElementById("network-status");
const worldOverlay = document.querySelector(".world-overlay");
const backButton = document.getElementById("world-back");
const globeState = new GlobeState();
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
	commerceWorld = new CommerceWorld(container, { region });
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
		onNodeSelected(region) {
			const resolvedRegion = regions[region.id];
			if (resolvedRegion) showCommerceWorld(resolvedRegion);
		},
	});
}

const eventClient = new EventClient({
	onStatus(status) {
		globeState.setConnected(status.connected);
		statusElement.textContent = status.connected
			? "LIVE EVENT STREAM"
			: "NETWORK READY";
		document.body.dataset.connected = String(status.connected);
	},

	onEvent(event) {
		const action = globeState.applyEvent(event);
		console.log("[Governor Event]", action);
	},
});

showGlobe();
backButton.addEventListener("click", showGlobe);

window.governorWorld = {
	globeState,
	eventClient,
	getGlobe: () => globe,
	getCommerceWorld: () => commerceWorld,
	showGlobe,
};
