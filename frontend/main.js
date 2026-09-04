import { Globe } from "./world/globe.js";
import { GlobeState } from "./world/globe-state.js";
import { EventClient } from "./world/event-client.js";

const container = document.getElementById("globe-container");
const statusElement = document.getElementById("network-status");
const globeState = new GlobeState();
const globe = new Globe(container);

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

window.governorWorld = {
	globe,
	globeState,
	eventClient,
};
