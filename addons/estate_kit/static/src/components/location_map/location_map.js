/** @odoo-module **/

import { Component, useState, useRef, onMounted, onWillUnmount } from "@odoo/owl";

const MAPGL_SCRIPT_URL = "https://mapgl.2gis.com/api/js/v1";
const DEFAULT_CENTER = [76.9453, 43.2385]; // Алматы [lng, lat]
const DEFAULT_ZOOM = 12;

let mapglLoadPromise = null;

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
            await this.loadMapglScript();
            await this.createMap();
            this.state.isLoading = false;
        } catch (error) {
            this.state.error = "Не удалось загрузить карту";
            this.state.isLoading = false;
            console.error("Map initialization error:", error);
        }
    }

    loadMapglScript() {
        if (mapglLoadPromise) {
            return mapglLoadPromise;
        }

        mapglLoadPromise = new Promise((resolve, reject) => {
            if (window.mapgl) {
                resolve();
                return;
            }

            const script = document.createElement("script");
            script.src = MAPGL_SCRIPT_URL;
            script.async = true;
            script.onload = () => {
                if (window.mapgl) {
                    resolve();
                } else {
                    mapglLoadPromise = null;
                    reject(new Error("mapgl global not found after load"));
                }
            };
            script.onerror = () => {
                mapglLoadPromise = null;
                reject(new Error("2GIS MapGL script fetch failed"));
            };
            document.head.appendChild(script);
        });

        return mapglLoadPromise;
    }

    createMap() {
        if (!this.mapContainer.el) {
            throw new Error("Map container not ready");
        }

        const center = this.getCenter();

        this.map = new mapgl.Map(this.mapContainer.el, {
            center,
            zoom: this.hasCoordinates() ? 16 : DEFAULT_ZOOM,
            key: this.props.apiKey,
        });

        if (this.hasCoordinates()) {
            this.addMarker(center);
        }

        if (!this.props.readonly) {
            this.map.on("click", (event) => {
                const coords = event.lngLat; // [lng, lat]
                this.onMapClick(coords);
            });
        }
    }

    destroyMap() {
        if (this.marker) {
            this.marker.destroy();
            this.marker = null;
        }
        if (this.map) {
            this.map.destroy();
            this.map = null;
        }
    }

    hasCoordinates() {
        return this.props.latitude && this.props.longitude;
    }

    getCenter() {
        if (this.hasCoordinates()) {
            return [this.props.longitude, this.props.latitude]; // [lng, lat]
        }
        return DEFAULT_CENTER;
    }

    addMarker(coords) {
        // coords = [lng, lat]
        if (this.marker) {
            this.marker.destroy();
            this.marker = null;
        }

        this.marker = new mapgl.Marker(this.map, {
            coordinates: coords,
        });
    }

    onMapClick(coords) {
        // coords = [lng, lat]
        if (this.props.readonly) return;

        this.addMarker(coords);
        this.map.setCenter(coords);

        if (this.props.onLocationChange) {
            this.props.onLocationChange({
                latitude: coords[1],
                longitude: coords[0],
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
            const data = json.result || {};

            if (data.error || data.lat === undefined || data.lon === undefined) {
                this.state.error = data.error === "not_found" ? "Адрес не найден" : "Ошибка геокодирования";
                setTimeout(() => { this.state.error = null; }, 3000);
                this.state.isGeocoding = false;
                return;
            }

            const lat = parseFloat(data.lat);
            const lng = parseFloat(data.lon);

            this.addMarker([lng, lat]);
            this.map.setCenter([lng, lat]);
            this.map.setZoom(16);

            if (this.props.onLocationChange) {
                this.props.onLocationChange({ latitude: lat, longitude: lng });
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
            this.addMarker([longitude, latitude]);
            this.map.setCenter([longitude, latitude]);
            this.map.setZoom(16);
        }
    }
}
