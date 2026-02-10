/** @odoo-module **/

import { Component, useState, useRef, onMounted, onWillUnmount } from "@odoo/owl";

const MAPGL_API_URL = "https://mapgl.2gis.com/api/js/v1";
const GEOCODER_API_URL = "https://catalog.api.2gis.com/3.0/items/geocode";
const DEFAULT_CENTER = [76.9453, 43.2385]; // Алматы
const DEFAULT_ZOOM = 12;

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
            await this.loadMapGLScript();
            this.createMap();
            this.state.isLoading = false;
        } catch (error) {
            this.state.error = "Не удалось загрузить карту";
            this.state.isLoading = false;
            console.error("Map initialization error:", error);
        }
    }

    loadMapGLScript() {
        return new Promise((resolve, reject) => {
            if (window.mapgl) {
                resolve();
                return;
            }

            const script = document.createElement("script");
            script.src = MAPGL_API_URL;
            script.async = true;
            script.onload = () => {
                if (window.mapgl) {
                    resolve();
                } else {
                    reject(new Error("MapGL not loaded"));
                }
            };
            script.onerror = () => reject(new Error("Script load failed"));
            document.head.appendChild(script);
        });
    }

    createMap() {
        if (!this.mapContainer.el) {
            throw new Error("Map container not ready");
        }

        const center = this.getCenter();

        this.map = new window.mapgl.Map(this.mapContainer.el, {
            center: center,
            zoom: this.hasCoordinates() ? 16 : DEFAULT_ZOOM,
            key: this.props.apiKey,
        });

        if (this.hasCoordinates()) {
            this.addMarker(center);
        }

        if (!this.props.readonly) {
            this.map.on("click", (ev) => this.onMapClick(ev));
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
            return [this.props.longitude, this.props.latitude];
        }
        return DEFAULT_CENTER;
    }

    addMarker(coords) {
        if (this.marker) {
            this.marker.destroy();
        }

        this.marker = new window.mapgl.Marker(this.map, {
            coordinates: coords,
        });
    }

    onMapClick(ev) {
        if (this.props.readonly) return;

        const coords = ev.lngLat;
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
        if (!this.props.geoAddress || !this.props.apiKey) return;

        this.state.isGeocoding = true;

        try {
            const response = await fetch(
                `${GEOCODER_API_URL}?q=${encodeURIComponent(this.props.geoAddress)}&key=${this.props.apiKey}&fields=items.point`
            );
            const data = await response.json();

            if (data.result && data.result.items && data.result.items.length > 0) {
                const point = data.result.items[0].point;
                const coords = [point.lon, point.lat];

                this.addMarker(coords);
                this.map.setCenter(coords);
                this.map.setZoom(16);

                if (this.props.onLocationChange) {
                    this.props.onLocationChange({
                        latitude: point.lat,
                        longitude: point.lon,
                    });
                }
            } else {
                this.state.error = "Адрес не найден";
                setTimeout(() => {
                    this.state.error = null;
                }, 3000);
            }
        } catch (error) {
            console.error("Geocoding error:", error);
            this.state.error = "Ошибка геокодирования";
            setTimeout(() => {
                this.state.error = null;
            }, 3000);
        }

        this.state.isGeocoding = false;
    }

    updateMarkerPosition(latitude, longitude) {
        if (!this.map) return;

        if (latitude && longitude) {
            const coords = [longitude, latitude];
            this.addMarker(coords);
            this.map.setCenter(coords);
            this.map.setZoom(16);
        }
    }
}
