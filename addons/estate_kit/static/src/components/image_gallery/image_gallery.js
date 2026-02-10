/** @odoo-module **/

import { Component, useState } from "@odoo/owl";

export class ImageGallery extends Component {
    static template = "estate_kit.ImageGallery";
    static props = {
        images: Array,
        thumbnailSize: { type: Array, optional: true },
        onImageClick: Function,
        onReorder: Function,
        readonly: { type: Boolean, optional: true },
    };

    setup() {
        this.state = useState({
            draggedId: null,
            dragOverId: null,
            dragPosition: null,
        });
    }

    get thumbnailSize() {
        return this.props.thumbnailSize || [150, 150];
    }

    onDragStart(ev, image) {
        if (this.props.readonly) return;

        this.state.draggedId = image.id;
        ev.dataTransfer.effectAllowed = "move";
        ev.dataTransfer.setData("text/plain", image.id.toString());
        ev.currentTarget.classList.add("o_dragging");
    }

    onDragEnd(ev) {
        ev.currentTarget.classList.remove("o_dragging");
        this.state.draggedId = null;
        this.state.dragOverId = null;
        this.state.dragPosition = null;
    }

    onDragOver(ev, image) {
        if (this.props.readonly || image.id === this.state.draggedId) return;

        ev.preventDefault();
        ev.dataTransfer.dropEffect = "move";

        const rect = ev.currentTarget.getBoundingClientRect();
        const midX = rect.left + rect.width / 2;
        const position = ev.clientX < midX ? "before" : "after";

        this.state.dragOverId = image.id;
        this.state.dragPosition = position;
    }

    onDragLeave() {
        this.state.dragOverId = null;
        this.state.dragPosition = null;
    }

    onDrop(ev, targetImage) {
        ev.preventDefault();

        if (this.state.draggedId && targetImage.id !== this.state.draggedId) {
            this.props.onReorder(
                this.state.draggedId,
                targetImage.id,
                this.state.dragPosition
            );
        }

        this.state.draggedId = null;
        this.state.dragOverId = null;
        this.state.dragPosition = null;
    }

    getItemClass(image) {
        const classes = ["o_image_gallery_item"];

        if (image.is_main) {
            classes.push("o_is_main");
        }
        if (this.state.draggedId === image.id) {
            classes.push("o_dragging");
        }
        if (this.state.dragOverId === image.id) {
            classes.push("o_drag_over");
            classes.push(`o_drag_${this.state.dragPosition}`);
        }

        return classes.join(" ");
    }
}
