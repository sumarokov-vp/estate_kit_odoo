/** @odoo-module **/

import { Component, useState, useRef, onMounted, onWillUnmount } from "@odoo/owl";

const YMAPS_PROXY_URL = "/estate_kit/ymaps.js";
const DEFAULT_CENTER = [43.2385, 76.9453]; // Алматы [lat, lng]
const DEFAULT_ZOOM = 12;

let ymapsLoadPromise = null;

export class LocationMap extends Component {
    static template = "estate_kit.LocationMap";
    static props = {
        latitude: { type: Number, optional: true },
        longitude: { type: Number, optional: true },
        geoAddress: { type: String, optional: true },
        apiKey: { type: String },
        readonly: { type: Boolean, optional: true },
        onLocationChange: { type: Function, optional: true },
    };

    setup() {
        this.mapContainer = useRef("mapContainer");
        this.map = null;
        this.marker = null;

        this.state = useState({
            isLoading: true,
            error: null,
            isGeocoding: false,
        });

        onMounted(() => this.initMap());
        onWillUnmount(() => this.destroyMap());
    }

    async initMap() {
        try {
            await this.loadYmapsScript();
            await this.createMap();
            this.state.isLoading = false;
        } catch (error) {
            this.state.error = "Не удалось загрузить карту";
            this.state.isLoading = false;
            console.error("Map initialization error:", error);
        }
    }

    loadYmapsScript() {
        if (ymapsLoadPromise) {
            return ymapsLoadPromise;
        }

        ymapsLoadPromise = new Promise((resolve, reject) => {
            if (window.ymaps3) {
                resolve();
                return;
            }

            // The proxy endpoint returns a small loader that injects the real
            // Yandex CDN script. We need to wait for ymaps3 to appear on window.
            const script = document.createElement("script");
            script.type = "text/javascript";
            script.src = YMAPS_PROXY_URL;
            script.onerror = () => {
                ymapsLoadPromise = null;
                reject(new Error("Yandex Maps loader fetch failed"));
            };
            document.head.appendChild(script);

            const timeout = 15000;
            const interval = 100;
            let elapsed = 0;
            const poll = setInterval(async () => {
                elapsed += interval;
                if (window.ymaps3) {
                    clearInterval(poll);
                    try {
                        await ymaps3.ready;
                        resolve();
                    } catch (e) {
                        ymapsLoadPromise = null;
                        reject(e);
                    }
                } else if (elapsed >= timeout) {
                    clearInterval(poll);
                    ymapsLoadPromise = null;
                    reject(new Error("Yandex Maps load timeout"));
                }
            }, interval);
        });

        return ymapsLoadPromise;
    }

    async createMap() {
        if (!this.mapContainer.el) {
            throw new Error("Map container not ready");
        }

        const center = this.getCenter();

        this.map = new ymaps3.YMap(this.mapContainer.el, {
            location: {
                center: [center[1], center[0]], // v3 uses [lng, lat]
                zoom: this.hasCoordinates() ? 16 : DEFAULT_ZOOM,
            },
        });

        this.map.addChild(new ymaps3.YMapDefaultSchemeLayer());
        this.map.addChild(new ymaps3.YMapDefaultFeaturesLayer());

        if (this.hasCoordinates()) {
            this.addMarker(center);
        }

        if (!this.props.readonly) {
            const clickHandler = new ymaps3.YMapListener({
                layer: "any",
                onClick: (_, event) => {
                    const coords = event.coordinates; // [lng, lat]
                    this.onMapClick([coords[1], coords[0]]);
                },
            });
            this.map.addChild(clickHandler);
        }
    }

    destroyMap() {
        if (this.map) {
            this.map.destroy();
            this.map = null;
            this.marker = null;
        }
    }

    hasCoordinates() {
        return this.props.latitude && this.props.longitude;
    }

    getCenter() {
        if (this.hasCoordinates()) {
            return [this.props.latitude, this.props.longitude]; // [lat, lng]
        }
        return DEFAULT_CENTER;
    }

    addMarker(coords) {
        // coords = [lat, lng]
        if (this.marker) {
            this.map.removeChild(this.marker);
        }

        const el = document.createElement("div");
        el.style.cssText =
            "width:24px;height:24px;background:#f00;border-radius:50%;border:3px solid #fff;" +
            "box-shadow:0 2px 6px rgba(0,0,0,.3);transform:translate(-50%,-50%)";

        this.marker = new ymaps3.YMapMarker(
            { coordinates: [coords[1], coords[0]] }, // [lng, lat]
            el
        );
        this.map.addChild(this.marker);
    }

    onMapClick(coords) {
        // coords = [lat, lng]
        if (this.props.readonly) return;

        this.addMarker(coords);
        this.map.setLocation({
            center: [coords[1], coords[0]],
            duration: 300,
        });

        if (this.props.onLocationChange) {
            this.props.onLocationChange({
                latitude: coords[0],
                longitude: coords[1],
            });
        }
    }

    async onGeocodeClick() {
        if (!this.props.geoAddress) return;

        this.state.isGeocoding = true;

        try {
            const resp = await fetch("/estate_kit/geocode", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    jsonrpc: "2.0",
                    method: "call",
                    params: { address: this.props.geoAddress },
                }),
            });
            const json = await resp.json();
            const data = json.result;

            if (data.error) {
                this.state.error = data.error;
                setTimeout(() => { this.state.error = null; }, 3000);
                this.state.isGeocoding = false;
                return;
            }

            const featureMember =
                data.response?.GeoObjectCollection?.featureMember;
            if (featureMember && featureMember.length > 0) {
                const pos = featureMember[0].GeoObject.Point.pos.split(" ");
                const lng = parseFloat(pos[0]);
                const lat = parseFloat(pos[1]);

                this.addMarker([lat, lng]);
                this.map.setLocation({
                    center: [lng, lat],
                    zoom: 16,
                    duration: 300,
                });

                if (this.props.onLocationChange) {
                    this.props.onLocationChange({ latitude: lat, longitude: lng });
                }
            } else {
                this.state.error = "Адрес не найден";
                setTimeout(() => { this.state.error = null; }, 3000);
            }
        } catch (error) {
            console.error("Geocoding error:", error);
            this.state.error = "Ошибка геокодирования";
            setTimeout(() => { this.state.error = null; }, 3000);
        }

        this.state.isGeocoding = false;
    }

    updateMarkerPosition(latitude, longitude) {
        if (!this.map) return;

        if (latitude && longitude) {
            this.addMarker([latitude, longitude]);
            this.map.setLocation({
                center: [longitude, latitude],
                zoom: 16,
                duration: 300,
            });
        }
    }
}
