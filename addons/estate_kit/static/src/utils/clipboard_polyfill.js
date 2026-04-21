/** @odoo-module **/

import { registry } from "@web/core/registry";
import { browser } from "@web/core/browser/browser";

function applyPolyfill(nav) {
    if (!nav) {
        return;
    }
    if (nav.clipboard && typeof nav.clipboard.writeText === "function") {
        return;
    }

    const fallback = {
        writeText(text) {
            return new Promise((resolve, reject) => {
                const ta = document.createElement("textarea");
                ta.value = String(text == null ? "" : text);
                ta.setAttribute("readonly", "");
                ta.style.position = "fixed";
                ta.style.top = "0";
                ta.style.left = "0";
                ta.style.opacity = "0";
                ta.style.pointerEvents = "none";
                document.body.appendChild(ta);
                ta.select();
                ta.setSelectionRange(0, ta.value.length);
                let ok = false;
                try {
                    ok = document.execCommand("copy");
                } catch (err) {
                    document.body.removeChild(ta);
                    reject(err);
                    return;
                }
                document.body.removeChild(ta);
                if (ok) {
                    resolve();
                } else {
                    reject(new Error("execCommand('copy') failed"));
                }
            });
        },
        readText() {
            return Promise.reject(
                new Error("Clipboard readText not available in insecure context")
            );
        },
    };

    try {
        Object.defineProperty(nav, "clipboard", {
            value: fallback,
            configurable: true,
            writable: true,
        });
    } catch (e) {
        nav.clipboard = fallback;
    }
}

registry.category("services").add("estate_kit.clipboard_polyfill", {
    start() {
        applyPolyfill(browser.navigator);
        applyPolyfill(window.navigator);
    },
});
