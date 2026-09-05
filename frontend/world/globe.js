import * as THREE from "three";
import { OrbitControls } from "https://cdn.jsdelivr.net/npm/three@0.180.0/examples/jsm/controls/OrbitControls.js";

export class Globe {
	constructor(container, { onNodeSelected = () => { } } = {}) {
		if (!container) {
			throw new Error("Globe container is required.");
		}

		this.container = container;
		this.onNodeSelected = onNodeSelected;
		this.scene = new THREE.Scene();
		this.camera = new THREE.PerspectiveCamera(
			42,
			container.clientWidth / container.clientHeight,
			0.1,
			100,
		);
		this.camera.position.set(0, 0.2, 3.8);

		this.renderer =
			new THREE.WebGLRenderer({
				antialias: true,
				alpha: true,
			});
		this.renderer.setPixelRatio(
			Math.min(window.devicePixelRatio, 2),
		);
		this.renderer.setSize(
			container.clientWidth,
			container.clientHeight,
		);
		container.appendChild(
			this.renderer.domElement,
		);
		this.raycaster = new THREE.Raycaster();
		this.pointer = new THREE.Vector2();
		this.handlePointerDown =
			this.handlePointerDown.bind(this);
		this.renderer.domElement.addEventListener(
			"pointerdown",
			this.handlePointerDown,
		);
		this.controls =
			new OrbitControls(
				this.camera,
				this.renderer.domElement,
			);
		this.controls.enableDamping = true;
		this.controls.enablePan = false;
		this.controls.minDistance = 2.5;
		this.controls.maxDistance = 6;
		this.controls.autoRotate = true;
		this.controls.autoRotateSpeed = 0.6;

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
        {
            id: "mumbai",
            label: "MUMBAI",
            lat: 19.076,
            lon: 72.8777,
        },
        {
            id: "singapore",
            label: "SINGAPORE",
            lat: 1.3521,
            lon: 103.8198,
        },
        {
            id: "tokyo",
            label: "TOKYO",
            lat: 35.6762,
            lon: 139.6503,
        },
        {
            id: "dubai",
            label: "DUBAI",
            lat: 25.2048,
            lon: 55.2708,
        },
        {
            id: "london",
            label: "LONDON",
            lat: 51.5074,
            lon: -0.1278,
        },
        {
            id: "frankfurt",
            label: "FRANKFURT",
            lat: 50.1109,
            lon: 8.6821,
        },
        {
            id: "new-york",
            label: "NEW YORK",
            lat: 40.7128,
            lon: -74.006,
        },
        {
            id: "san-francisco",
            label: "SAN FRANCISCO",
            lat: 37.7749,
            lon: -122.4194,
        },
        {
            id: "sao-paulo",
            label: "SAO PAULO",
            lat: -23.5505,
            lon: -46.6333,
        },
    ];

    for (const node of nodes) {
        const mesh = new THREE.Mesh(
            new THREE.SphereGeometry(
                0.06,
                20,
                20,
            ),
            new THREE.MeshBasicMaterial({
                color: 0xffffff,
            }),
        );

        mesh.position.copy(
            this.latLonToVector3(
                node.lat,
                node.lon,
                1.59,
            ),
        );

        mesh.userData.node = node;

        this.nodeGroup.add(mesh);

        const label = this.createNodeLabel(
            node.label,
        );

        label.position.copy(
            this.latLonToVector3(
                node.lat,
                node.lon,
                1.70,
            ),
        );

        /*
         * Labels are visual only.
         * Do not put them into the raycast target group.
         */
        this.globeGroup.add(label);
    }
}

	createNodeLabel(text) {
		const canvas =
			document.createElement("canvas");

		canvas.width = 512;
		canvas.height = 128;

		const context =
			canvas.getContext("2d");

		context.clearRect(
			0,
			0,
			canvas.width,
			canvas.height,
		);

		context.fillStyle =
			"rgba(255,255,255,0.9)";

		context.font =
			"700 28px Arial";

		context.textAlign =
			"center";

		context.textBaseline =
			"middle";

		context.fillText(
			text,
			canvas.width / 2,
			canvas.height / 2,
		);

		const texture =
			new THREE.CanvasTexture(
				canvas,
			);

		texture.needsUpdate =
			true;

		const material =
			new THREE.SpriteMaterial({
				map: texture,
				transparent: true,
				depthWrite: false,
			});

		const sprite =
			new THREE.Sprite(
				material,
			);

		sprite.scale.set(
			0.75,
			0.19,
			1,
		);

		return sprite;
	}

	latLonToVector3(lat, lon, radius) {
		const phi = THREE.MathUtils.degToRad(90 - lat);
		const theta = THREE.MathUtils.degToRad(lon + 180);
		const x = -(radius * Math.sin(phi) * Math.cos(theta));
		const z = radius * Math.sin(phi) * Math.sin(theta);
		const y = radius * Math.cos(phi);
		return new THREE.Vector3(x, y, z);
	}

	handlePointerDown(event) {
    const rect =
        this.renderer.domElement.getBoundingClientRect();

    this.pointer.x =
        ((event.clientX - rect.left) /
            rect.width) * 2 - 1;

    this.pointer.y =
        -((event.clientY - rect.top) /
            rect.height) * 2 + 1;

    this.raycaster.setFromCamera(
        this.pointer,
        this.camera,
    );

    const intersections =
        this.raycaster.intersectObjects(
            this.nodeGroup.children,
            false,
        );

    if (!intersections.length) {
        return;
    }

    const node =
        intersections[0].object.userData.node;

    if (!node) {
        return;
    }

    console.log(
        "[Globe Node Selected]",
        node,
    );

    this.onNodeSelected(node);
}

	handleResize() {
		if (!this.container) return;
		const width = this.container.clientWidth;
		const height = this.container.clientHeight;
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
		this.renderer.domElement.removeEventListener(
			"pointerdown",
			this.handlePointerDown,
		);
		if (this.renderer.domElement.parentNode) {
			this.renderer.domElement.parentNode.removeChild(this.renderer.domElement);
		}
		this.renderer.dispose();
	}
}

