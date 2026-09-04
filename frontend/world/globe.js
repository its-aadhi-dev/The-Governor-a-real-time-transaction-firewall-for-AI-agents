import * as THREE from "https://cdn.jsdelivr.net/npm/three@0.180.0/build/three.module.js";
import { OrbitControls } from "https://cdn.jsdelivr.net/npm/three@0.180.0/examples/jsm/controls/OrbitControls.js";

export class Globe {
	constructor(container) {
		if (!container) {
			throw new Error("Globe container is required.");
		}

		this.container = container;
		this.scene = new THREE.Scene();
		this.camera = new THREE.PerspectiveCamera(
			42,
			container.clientWidth / container.clientHeight,
			0.1,
			100,
		);
		this.camera.position.set(0, 0.2, 3.8);

		this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
		this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
		this.renderer.setSize(container.clientWidth, container.clientHeight);
		container.appendChild(this.renderer.domElement);

		this.controls = new OrbitControls(this.camera, this.renderer.domElement);
		this.controls.enableDamping = true;
		this.controls.enablePan = false;
		this.controls.minDistance = 2.5;
		this.controls.maxDistance = 6;
		this.controls.autoRotate = true;
		this.controls.autoRotateSpeed = 0.25;

		this.globeGroup = new THREE.Group();
		this.nodeGroup = new THREE.Group();
		this.scene.add(this.globeGroup, this.nodeGroup);

		this.createLighting();
		this.createGlobe();
		this.createAtmosphere();
		this.createGrid();
		this.createCommerceNodes();

		this.handleResize = this.handleResize.bind(this);
		window.addEventListener("resize", this.handleResize);
		this.animate();
	}

	createLighting() {
		this.scene.add(new THREE.AmbientLight(0xffffff, 1.6));
		const key = new THREE.DirectionalLight(0xffffff, 2.5);
		key.position.set(4, 3, 5);
		this.scene.add(key);
	}

	createGlobe() {
		this.globeGroup.add(new THREE.Mesh(
			new THREE.SphereGeometry(1.55, 96, 64),
			new THREE.MeshStandardMaterial({
				color: 0x152238,
				roughness: 0.78,
				metalness: 0.08,
			}),
		));
	}

	createAtmosphere() {
		this.globeGroup.add(new THREE.Mesh(
			new THREE.SphereGeometry(1.62, 96, 64),
			new THREE.MeshBasicMaterial({
				color: 0x4ca6ff,
				transparent: true,
				opacity: 0.075,
				side: THREE.BackSide,
			}),
		));
	}

	createGrid() {
		const material = new THREE.LineBasicMaterial({
			color: 0x3b6e91,
			transparent: true,
			opacity: 0.35,
		});
		const radius = 1.565;

		for (let latitude = -60; latitude <= 60; latitude += 20) {
			const points = [];
			const lat = THREE.MathUtils.degToRad(latitude);
			const y = radius * Math.sin(lat);
			const ringRadius = radius * Math.cos(lat);
			for (let i = 0; i <= 128; i += 1) {
				const theta = (i / 128) * Math.PI * 2;
				points.push(new THREE.Vector3(
					ringRadius * Math.cos(theta),
					y,
					ringRadius * Math.sin(theta),
				));
			}
			this.globeGroup.add(new THREE.Line(
				new THREE.BufferGeometry().setFromPoints(points),
				material,
			));
		}

		for (let longitude = 0; longitude < 180; longitude += 20) {
			const pointsA = [];
			const pointsB = [];
			const lon = THREE.MathUtils.degToRad(longitude);
			for (let i = 0; i <= 64; i += 1) {
				const latitude = -Math.PI / 2 + (i / 64) * Math.PI;
				const x = radius * Math.cos(latitude) * Math.cos(lon);
				const y = radius * Math.sin(latitude);
				const z = radius * Math.cos(latitude) * Math.sin(lon);
				pointsA.push(new THREE.Vector3(x, y, z));
				pointsB.push(new THREE.Vector3(-x, y, -z));
			}
			for (const points of [pointsA, pointsB]) {
				this.globeGroup.add(new THREE.Line(
					new THREE.BufferGeometry().setFromPoints(points),
					material,
				));
			}
		}
	}

	createCommerceNodes() {
		const nodes = [
			{ id: "asia", label: "ASIA", lat: 20, lon: 100 },
			{ id: "europe", label: "EUROPE", lat: 50, lon: 15 },
			{ id: "americas", label: "AMERICAS", lat: 35, lon: -100 },
		];
		for (const node of nodes) {
			const mesh = new THREE.Mesh(
				new THREE.SphereGeometry(0.035, 16, 16),
				new THREE.MeshBasicMaterial({ color: 0xffffff }),
			);
			mesh.position.copy(this.latLonToVector3(node.lat, node.lon, 1.59));
			mesh.userData.node = node;
			this.nodeGroup.add(mesh);
		}
	}

	latLonToVector3(lat, lon, radius) {
		const phi = THREE.MathUtils.degToRad(90 - lat);
		const theta = THREE.MathUtils.degToRad(lon + 180);
		return new THREE.Vector3(
			-radius * Math.sin(phi) * Math.cos(theta),
			radius * Math.cos(phi),
			radius * Math.sin(phi) * Math.sin(theta),
		);
	}

	handleResize() {
		const width = this.container.clientWidth;
		const height = this.container.clientHeight;
		if (!width || !height) return;
		this.camera.aspect = width / height;
		this.camera.updateProjectionMatrix();
		this.renderer.setSize(width, height);
	}

	animate() {
		requestAnimationFrame(() => this.animate());
		this.controls.update();
		this.renderer.render(this.scene, this.camera);
	}

	destroy() {
		window.removeEventListener("resize", this.handleResize);
		this.controls.dispose();
		this.renderer.dispose();
	}
}
