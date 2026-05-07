const csrfToken = document.querySelector("[name=csrfmiddlewaretoken]")?.value;
const barcodeInput = document.getElementById("barcode-input");
const feedback = document.getElementById("scan-feedback");
const cartBody = document.querySelector("#cart-table tbody");
const subtotalEl = document.getElementById("subtotal");
const taxEl = document.getElementById("tax");
const totalEl = document.getElementById("total");
const cartCountEl = document.getElementById("cart-count");
const checkoutForm = document.getElementById("checkout-form");
const clearCartButton = document.getElementById("clear-cart");
const cameraButton = document.getElementById("toggle-camera");
const cameraPanel = document.getElementById("camera-panel");
const cameraPreview = document.getElementById("camera-preview");

let videoStream = null;
let detector = null;
let scanLoopHandle = null;

function setFeedback(message, isError = false) {
    feedback.textContent = message;
    feedback.style.background = isError ? "rgba(185, 28, 28, 0.12)" : "rgba(12, 124, 89, 0.1)";
    feedback.style.color = isError ? "#991b1b" : "#085d43";
}

function currency(value) {
    return `$${Number(value).toFixed(2)}`;
}

function renderCart(items, totals) {
    if (!items.length) {
        cartBody.innerHTML = '<tr class="empty-cart-row"><td colspan="4">No scanned items yet.</td></tr>';
    } else {
        cartBody.innerHTML = items.map((item) => `
            <tr data-product-id="${item.product_id}">
                <td>${item.name}<br><small>${item.barcode}</small></td>
                <td><input type="number" min="0" value="${item.quantity}" class="qty-input"></td>
                <td>${currency(item.unit_price)}</td>
                <td>${currency(item.subtotal)}</td>
            </tr>
        `).join("");
    }

    cartCountEl.textContent = `${items.length} item(s)`;
    subtotalEl.textContent = currency(totals.subtotal);
    taxEl.textContent = currency(totals.tax);
    totalEl.textContent = currency(totals.total);
}

async function postForm(url, body) {
    const response = await fetch(url, {
        method: "POST",
        headers: {
            "X-CSRFToken": csrfToken,
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
        },
        body: new URLSearchParams(body),
    });
    const data = await response.json();
    if (!response.ok) {
        throw new Error(data.error || "Request failed.");
    }
    return data;
}

barcodeInput?.addEventListener("keydown", async (event) => {
    if (event.key !== "Enter") {
        return;
    }
    event.preventDefault();
    const barcode = barcodeInput.value.trim();
    if (!barcode) {
        return;
    }
    try {
        const data = await postForm("/terminal/scan/", { barcode });
        const row = cartBody.querySelector(`[data-product-id="${data.item.product_id}"]`);
        let items = [];
        if (row) {
            items = Array.from(cartBody.querySelectorAll("tr[data-product-id]")).map((tr) => ({
                product_id: Number(tr.dataset.productId),
                name: tr.cells[0].childNodes[0].textContent,
                barcode: tr.cells[0].querySelector("small")?.textContent || "",
                quantity: Number(tr.querySelector(".qty-input")?.value || 0),
                unit_price: tr.cells[2].textContent.replace("$", ""),
                subtotal: tr.cells[3].textContent.replace("$", ""),
            }));
            const index = items.findIndex((item) => item.product_id === data.item.product_id);
            items[index] = data.item;
        } else {
            items = [{ ...data.item }, ...Array.from(cartBody.querySelectorAll("tr[data-product-id]")).map((tr) => ({
                product_id: Number(tr.dataset.productId),
                name: tr.cells[0].childNodes[0].textContent,
                barcode: tr.cells[0].querySelector("small")?.textContent || "",
                quantity: Number(tr.querySelector(".qty-input")?.value || 0),
                unit_price: tr.cells[2].textContent.replace("$", ""),
                subtotal: tr.cells[3].textContent.replace("$", ""),
            }))];
        }
        renderCart(items, data.totals);
        barcodeInput.value = "";
        setFeedback(`Scanned ${data.item.name}`);
        barcodeInput.focus();
    } catch (error) {
        setFeedback(error.message, true);
        barcodeInput.select();
    }
});

cartBody?.addEventListener("change", async (event) => {
    const target = event.target;
    if (!(target instanceof HTMLInputElement) || !target.classList.contains("qty-input")) {
        return;
    }
    const row = target.closest("tr");
    if (!row) {
        return;
    }
    try {
        const data = await postForm(`/terminal/cart/${row.dataset.productId}/`, { quantity: target.value });
        renderCart(data.items, data.totals);
        setFeedback("Cart updated.");
    } catch (error) {
        setFeedback(error.message, true);
    }
});

checkoutForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    try {
        const formData = new FormData(checkoutForm);
        const data = await postForm("/terminal/checkout/", Object.fromEntries(formData.entries()));
        window.location.href = data.receipt_url;
    } catch (error) {
        setFeedback(error.message, true);
    }
});

clearCartButton?.addEventListener("click", async () => {
    try {
        await postForm("/terminal/cart/clear/", {});
        renderCart([], { subtotal: 0, tax: 0, total: 0 });
        setFeedback("Cart cleared.");
        barcodeInput.focus();
    } catch (error) {
        setFeedback(error.message, true);
    }
});

async function stopCamera() {
    if (scanLoopHandle) {
        cancelAnimationFrame(scanLoopHandle);
        scanLoopHandle = null;
    }
    if (videoStream) {
        videoStream.getTracks().forEach((track) => track.stop());
        videoStream = null;
    }
    cameraPanel.classList.add("hidden");
}

async function processCameraFrame() {
    if (!detector || !cameraPreview.srcObject) {
        return;
    }
    try {
        const barcodes = await detector.detect(cameraPreview);
        if (barcodes.length) {
            barcodeInput.value = barcodes[0].rawValue;
            barcodeInput.dispatchEvent(new KeyboardEvent("keydown", { key: "Enter" }));
            await stopCamera();
            return;
        }
    } catch (error) {
        setFeedback("Camera scan unavailable in this browser.", true);
        await stopCamera();
        return;
    }
    scanLoopHandle = requestAnimationFrame(processCameraFrame);
}

cameraButton?.addEventListener("click", async () => {
    if (cameraPanel.classList.contains("hidden")) {
        if (!("BarcodeDetector" in window)) {
            setFeedback("BarcodeDetector is not supported in this browser.", true);
            return;
        }
        detector = new window.BarcodeDetector({ formats: ["ean_13", "ean_8", "code_128", "upc_a", "upc_e"] });
        videoStream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" } });
        cameraPreview.srcObject = videoStream;
        await cameraPreview.play();
        cameraPanel.classList.remove("hidden");
        processCameraFrame();
    } else {
        await stopCamera();
    }
});

barcodeInput?.focus();
