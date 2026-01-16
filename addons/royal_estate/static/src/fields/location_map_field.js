/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, useState, onWillStart, onWillUpdateProps } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { LocationMap } from "../components/location_map/location_map";

export class LocationMapField extends Component {
    static template = "royal_estate.LocationMapField";
    static components = { LocationMap };
    static props = {
        ...standardFieldProps,
    };

    setup() {
        this.orm = useService("orm");

        this.state = useState({
            apiKey: "",
            latitude: 0,
            longitude: 0,
            geoAddress: "",
        });

        onWillStart(async () => {
            await this.loadApiKey();
            this.updateStateFromRecord(this.props);
        });

        onWillUpdateProps((nextProps) => {
            this.updateStateFromRecord(nextProps);
        });
    }

    async loadApiKey() {
        try {
            const result = await this.orm.call(
                "ir.config_parameter",
                "get_param",
                ["royal_estate.twogis_api_key", ""]
            );
            this.state.apiKey = result || "";
        } catch {
            console.error("Failed to load 2GIS API key");
        }
    }

    updateStateFromRecord(props) {
        const record = props.record;

        this.state.latitude = record.data.latitude || 0;
        this.state.longitude = record.data.longitude || 0;
        this.state.geoAddress = record.data.geo_address || "";
    }

    get readonly() {
        return this.props.readonly;
    }

    async onLocationChange(location) {
        if (this.readonly) return;

        await this.props.record.update({
            latitude: location.latitude,
            longitude: location.longitude,
        });

        this.state.latitude = location.latitude;
        this.state.longitude = location.longitude;
    }
}

export const locationMapField = {
    component: LocationMapField,
    supportedTypes: ["float"],
};

registry.category("fields").add("location_map", locationMapField);
