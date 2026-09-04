import * as THREE from "three";

export class CommerceWorld {
        constructor(container, { region, onMerchantSelected = () => {} }) {
                if (!container) {
                        throw new Error("Commerce world container is required.");
                }

                if (!region?.id) {
                        throw new Error("Commerce world requires a region.");
                }

                this.container = container;
                this.region = region;
                this.onMerchantSelected = onMerchantSelected;

                this.selectedMerchantId = null;
                this.selectedItemId = null;

                this.scene = new THREE.Scene();

                this.camera = new THREE.PerspectiveCamera(
                        50,
                        container.clientWidth / container.clientHeight,
                        0.1,
                        100,
                );

                this.camera.position.set(8, 7, 10);

                this.renderer = new THREE.WebGLRenderer({
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

                container.appendChild(this.renderer.domElement);

                this.clock = new THREE.Clock();
                this.world = new THREE.Group();

                this.scene.add(this.world);

                this.createLighting();
                this.createGround();
                this.createTerritory();
                this.createMarketCore();
                this.createPaths();
                this.createWorldMarkers();

                this.handleResize = this.handleResize.bind(this);
                this.handlePointer = this.handlePointer.bind(this);

                window.addEventListener("resize", this.handleResize);
                this.renderer.domElement.addEventListener(
                        "pointerdown",
                        this.handlePointer,
                );

                this.animate();
        }

        createLighting() {
                this.scene.add(
                        new THREE.HemisphereLight(
                                0xffffff,
                                0x0b1120,
                                2.4,
                        ),
                );

                const key = new THREE.DirectionalLight(
                        0xffffff,
                        2,
                );

                key.position.set(5, 10, 4);

                this.scene.add(key);
        }

        createGround() {
                const ground = new THREE.Mesh(
                        new THREE.PlaneGeometry(
                                28,
                                28,
                                28,
                                28,
                        ),
                        new THREE.MeshStandardMaterial({
                                color: 0x07111d,
                                roughness: 0.92,
                                metalness: 0.02,
                        }),
                );

                ground.rotation.x = -Math.PI / 2;

                this.world.add(ground);

                const grid = new THREE.GridHelper(
                        28,
                        28,
                        0x274258,
                        0x132435,
                );

                grid.position.y = 0.01;

                this.world.add(grid);
        }

        createTerritory() {
                const territory = new THREE.Mesh(
                        new THREE.CircleGeometry(6.4, 6),
                        new THREE.MeshBasicMaterial({
                                color: 0x0d2334,
                                transparent: true,
                                opacity: 0.75,
                                side: THREE.DoubleSide,
                        }),
                );

                territory.rotation.x = -Math.PI / 2;
                territory.position.y = 0.03;

                this.world.add(territory);

                const ring = new THREE.Mesh(
                        new THREE.RingGeometry(
                                6.15,
                                6.23,
                                96,
                        ),
                        new THREE.MeshBasicMaterial({
                                color: 0x559ac2,
                                transparent: true,
                                opacity: 0.32,
                                side: THREE.DoubleSide,
                        }),
                );

                ring.rotation.x = -Math.PI / 2;
                ring.position.y = 0.05;

                this.world.add(ring);
        }

        createMarketCore() {
                const platform = new THREE.Mesh(
                        new THREE.CylinderGeometry(
                                2.1,
                                2.35,
                                0.35,
                                8,
                        ),
                        new THREE.MeshStandardMaterial({
                                color: 0x102437,
                                roughness: 0.62,
                                metalness: 0.25,
                        }),
                );

                platform.position.y = 0.18;

                this.world.add(platform);

                const core = new THREE.Mesh(
                        new THREE.CylinderGeometry(
                                0.72,
                                1.15,
                                1.65,
                                8,
                        ),
                        new THREE.MeshStandardMaterial({
                                color: 0x173b54,
                                roughness: 0.48,
                                metalness: 0.3,
                        }),
                );

                core.position.y = 1.05;

                this.world.add(core);

                const beacon = new THREE.Mesh(
                        new THREE.CylinderGeometry(
                                0.08,
                                0.08,
                                2.4,
                                12,
                        ),
                        new THREE.MeshBasicMaterial({
                                color: 0xffffff,
                                transparent: true,
                                opacity: 0.7,
                        }),
                );

                beacon.position.y = 2.95;

                this.world.add(beacon);
        }

        createPaths() {
                const material = new THREE.MeshBasicMaterial({
                        color: 0x315970,
                        transparent: true,
                        opacity: 0.45,
                });

                for (const [x, z] of [
                        [0, -5.1],
                        [5.1, 0],
                        [0, 5.1],
                        [-5.1, 0],
                ]) {
                        const path = new THREE.Mesh(
                                new THREE.BoxGeometry(
                                        0.45,
                                        0.04,
                                        6,
                                ),
                                material,
                        );

                        path.position.set(
                                x * 0.45,
                                0.08,
                                z * 0.45,
                        );

                        if (Math.abs(x) > Math.abs(z)) {
                                path.rotation.y = Math.PI / 2;
                        }

                        this.world.add(path);
                }
        }

        createWorldMarkers() {
                const positions = [
                        [-4.4, 0.15, -3],
                        [4.4, 0.15, -3],
                        [4.4, 0.15, 3],
                        [-4.4, 0.15, 3],
                ];

                positions.forEach(([x, y, z], index) => {
                        const marker = new THREE.Mesh(
                                new THREE.BoxGeometry(
                                        0.7,
                                        0.7,
                                        0.7,
                                ),
                                new THREE.MeshStandardMaterial({
                                        color: 0xffffff,
                                }),
                        );

                        marker.position.set(x, y, z);
                        marker.rotation.y = index * Math.PI / 4;

                        marker.userData = {
                                type: "merchant-slot",
                                index,
                                regionId: this.region.id,

                                /*
                                 * Temporary stable identifiers for
                                 * the visualization layer.
                                 *
                                 * These do NOT authorize payment.
                                 */
                                merchantId:
                                        `merchant_${this.region.id}_${index + 1}`,
                        };

                        this.world.add(marker);
                });
        }

        handlePointer(event) {
                const rect =
                        this.renderer.domElement.getBoundingClientRect();

                const mouse = new THREE.Vector2(
                        ((event.clientX - rect.left) / rect.width) * 2 - 1,
                        -((event.clientY - rect.top) / rect.height) * 2 + 1,
                );

                const raycaster = new THREE.Raycaster();

                raycaster.setFromCamera(
                        mouse,
                        this.camera,
                );

                const objects = this.world.children.filter(
                        (child) =>
                                child.userData?.type ===
                                "merchant-slot",
                );

                const intersections =
                        raycaster.intersectObjects(
                                objects,
                                false,
                        );

                if (!intersections.length) {
                        return;
                }

                const marker =
                        intersections[0].object;

                const merchantId =
                        marker.userData.merchantId;

                this.selectedMerchantId = merchantId;

                this.onMerchantSelected({
                        merchantId,
                        regionId: this.region.id,
                        slotIndex: marker.userData.index,
                });
        }

        getSelection() {
                return {
                        merchantId: this.selectedMerchantId,
                        itemId: this.selectedItemId,
                        regionId: this.region.id,
                };
        }

        setItem(itemId) {
                this.selectedItemId = itemId;
        }

        handleResize() {
                const width =
                        this.container.clientWidth;

                const height =
                        this.container.clientHeight;

                if (!width || !height) {
                        return;
                }

                this.camera.aspect =
                        width / height;

                this.camera.updateProjectionMatrix();

                this.renderer.setSize(
                        width,
                        height,
                );
        }

        animate() {
                this.animationFrame =
                        requestAnimationFrame(
                                () => this.animate(),
                        );

                this.world.rotation.y =
                        Math.sin(
                                this.clock.getElapsedTime() * 0.08,
                        ) * 0.025;

                this.renderer.render(
                        this.scene,
                        this.camera,
                );
        }

        destroy() {
                cancelAnimationFrame(
                        this.animationFrame,
                );

                window.removeEventListener(
                        "resize",
                        this.handleResize,
                );

                this.renderer.domElement.removeEventListener(
                        "pointerdown",
                        this.handlePointer,
                );

                this.renderer.dispose();

                this.container.innerHTML = "";
        }
}

