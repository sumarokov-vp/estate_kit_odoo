/** @odoo-module **/

import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";
import { Component, useState, useRef, onWillUpdateProps } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { ImageGallery } from "../components/image_gallery/image_gallery";
import { ImageLightbox } from "../components/image_lightbox/image_lightbox";

export class ImageGalleryField extends Component {
    static template = "estate_kit.ImageGalleryField";
    static components = { ImageGallery };
    static props = {
        ...standardFieldProps,
    };

    setup() {
        this.orm = useService("orm");
        this.dialogService = useService("dialog");
        this.notification = useService("notification");

        this.state = useState({
            images: [],
            isLoading: true,
        });

        this.fileInput = useRef("fileInput");

        this.loadImages();

        onWillUpdateProps((nextProps) => {
            if (nextProps.record !== this.props.record) {
                this.loadImages(nextProps);
            }
        });
    }

    get thumbnailSize() {
        return [150, 150];
    }

    get readonly() {
        return this.props.readonly;
    }

    async loadImages(props = this.props) {
        this.state.isLoading = true;

        try {
            const propertyId = props.record.resId;
            if (!propertyId) {
                this.state.images = [];
                this.state.isLoading = false;
                return;
            }

            const images = await this.orm.searchRead(
                "estate.property.image",
                [["property_id", "=", propertyId]],
                ["id", "name", "sequence", "is_main"],
                { order: "sequence, id" }
            );

            this.state.images = images.map((img) => ({
                ...img,
                thumbnailUrl: `/web/image/estate.property.image/${img.id}/image?width=150&height=150`,
                fullUrl: `/web/image/estate.property.image/${img.id}/image`,
            }));
        } catch {
            this.state.images = [];
        }

        this.state.isLoading = false;
    }

    onImageClick(image, index) {
        this.dialogService.add(ImageLightbox, {
            images: this.state.images,
            initialIndex: index,
            onSetMain: this.readonly ? null : (imageId) => this.setMainImage(imageId),
            onDelete: this.readonly ? null : (imageId) => this.deleteImage(imageId),
        });
    }

    onAddImage() {
        if (this.fileInput.el) {
            this.fileInput.el.click();
        }
    }

    async onFileSelected(ev) {
        const files = ev.target.files;
        if (!files.length) return;

        for (const file of files) {
            await this.uploadImage(file);
        }

        ev.target.value = "";
        await this.loadImages();
    }

    async uploadImage(file) {
        const base64 = await this.fileToBase64(file);
        const propertyId = this.props.record.resId;

        await this.orm.create("estate.property.image", [
            {
                property_id: propertyId,
                name: file.name.replace(/\.[^/.]+$/, ""),
                image: base64.split(",")[1],
                sequence: (this.state.images.length + 1) * 10,
            },
        ]);

        this.notification.add("Фото добавлено", { type: "success" });
    }

    fileToBase64(file) {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = () => resolve(reader.result);
            reader.onerror = reject;
            reader.readAsDataURL(file);
        });
    }

    async setMainImage(imageId) {
        const allIds = this.state.images.map((img) => img.id);
        await this.orm.write("estate.property.image", allIds, { is_main: false });
        await this.orm.write("estate.property.image", [imageId], { is_main: true });
        await this.loadImages();
        this.notification.add("Главное фото установлено", { type: "success" });
    }

    async deleteImage(imageId) {
        await this.orm.unlink("estate.property.image", [imageId]);
        await this.loadImages();
        this.notification.add("Фото удалено", { type: "warning" });
    }

    async onReorder(draggedId, targetId, position) {
        const images = [...this.state.images];
        const draggedIndex = images.findIndex((img) => img.id === draggedId);
        const targetIndex = images.findIndex((img) => img.id === targetId);

        if (draggedIndex === -1 || targetIndex === -1) return;

        const [draggedItem] = images.splice(draggedIndex, 1);
        let insertIndex = targetIndex;
        if (position === "after") {
            insertIndex = draggedIndex < targetIndex ? targetIndex : targetIndex + 1;
        } else {
            insertIndex = draggedIndex < targetIndex ? targetIndex - 1 : targetIndex;
        }
        images.splice(insertIndex, 0, draggedItem);

        for (let i = 0; i < images.length; i++) {
            await this.orm.write("estate.property.image", [images[i].id], {
                sequence: (i + 1) * 10,
            });
        }

        await this.loadImages();
    }
}

export const imageGalleryField = {
    component: ImageGalleryField,
    supportedTypes: ["one2many"],
};

registry.category("fields").add("image_gallery", imageGalleryField);
