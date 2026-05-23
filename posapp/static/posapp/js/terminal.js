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
const checkoutModal = document.getElementById("checkout-modal");
const checkoutModalMessage = document.getElementById("checkout-modal-message");
const printThermalButton = document.getElementById("print-thermal");
const printA4Button = document.getElementById("print-a4");
const skipPrintButton = document.getElementById("skip-print");

let videoStream = null;
let detector = null;
let scanLoopHandle = null;
let isProcessingScan = false;
let barcodeTimeout = null;
let isCheckoutModalOpen = false;
let latestReceiptUrl = "";
let latestThermalReceiptUrl = "";
let latestA4ReceiptUrl = "";

function openCheckoutModal(receiptNumber, receiptUrl, thermalReceiptUrl, a4ReceiptUrl) {
    latestReceiptUrl = receiptUrl;
    latestThermalReceiptUrl = thermalReceiptUrl || `${receiptUrl}?format=thermal&paper=58`;
    latestA4ReceiptUrl = a4ReceiptUrl || `${receiptUrl}?format=pdf`;
    isCheckoutModalOpen = true;
    checkoutModalMessage.textContent = `Receipt ${receiptNumber} created. Print now?`;
    checkoutModal.classList.remove("hidden");
}

function closeCheckoutModal() {
    isCheckoutModalOpen = false;
    checkoutModal.classList.add("hidden");
}

function continueAfterCheckout() {
    closeCheckoutModal();
    renderCart([], { subtotal: 0, tax: 0, total: 0 });
    setFeedback("Checkout complete. Ready for next customer.");
    barcodeInput.focus();
}

function openPrintWindow(url) {
    const printWindow = window.open(url, "_blank", "noopener,noreferrer");
    if (!printWindow) {
        setFeedback("Popup blocked. Please allow popups to print receipt.", true);
    }
}

function setFeedback(message, isError = false) {
    feedback.textContent = message;
    feedback.style.background = isError ? "rgba(185, 28, 28, 0.12)" : "rgba(12, 124, 89, 0.1)";
    feedback.style.color = isError ? "#991b1b" : "#085d43";
}

function currency(value) {
    return `₱${Number(value).toFixed(2)}`;
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
    
    // Clear timeout if user presses Enter manually
    if (barcodeTimeout) {
        clearTimeout(barcodeTimeout);
        barcodeTimeout = null;
    }
    
    // Prevent double-scan in quick succession
    if (isProcessingScan) {
        return;
    }
    
    const barcode = barcodeInput.value.trim();
    if (!barcode) {
        return;
    }
    
    await submitBarcode(barcode);
});

// Auto-submit barcode when input is stable for 200ms (scanner detection)
barcodeInput?.addEventListener("input", (event) => {
    // Clear existing timeout
    if (barcodeTimeout) {
        clearTimeout(barcodeTimeout);
    }
    
    // Set new timeout - submit after 200ms of no input
    barcodeTimeout = setTimeout(async () => {
        const barcode = barcodeInput.value.trim();
        
        // Only auto-submit if:
        // 1. Input is not empty
        // 2. Not already processing
        // 3. Input looks like a barcode (at least 3 characters)
        if (barcode.length >= 3 && !isProcessingScan) {
            await submitBarcode(barcode);
        }
        
        barcodeTimeout = null;
    }, 200);
});

async function submitBarcode(barcode) {
    // Prevent double-scan in quick succession
    if (isProcessingScan) {
        return;
    }
    
    isProcessingScan = true;
    barcodeInput.disabled = true;
    setFeedback("Scanning...");
    
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
                unit_price: tr.cells[2].textContent.replace("₱", ""),
                subtotal: tr.cells[3].textContent.replace("₱", ""),
            }));
            const index = items.findIndex((item) => item.product_id === data.item.product_id);
            items[index] = data.item;
        } else {
            items = [{ ...data.item }, ...Array.from(cartBody.querySelectorAll("tr[data-product-id]")).map((tr) => ({
                product_id: Number(tr.dataset.productId),
                name: tr.cells[0].childNodes[0].textContent,
                barcode: tr.cells[0].querySelector("small")?.textContent || "",
                quantity: Number(tr.querySelector(".qty-input")?.value || 0),
                unit_price: tr.cells[2].textContent.replace("₱", ""),
                subtotal: tr.cells[3].textContent.replace("₱", ""),
            }))];
        }
        renderCart(items, data.totals);
        barcodeInput.value = "";
        
        // Stock check - show low stock warning (item was successfully added)
        const stock = Number(data.item.stock_quantity || 0);
        const remaining = stock - Number(data.item.quantity || 1);
        
        let feedbackMsg = `✓ ${data.item.name}`;
        let isWarning = false;
        
        if (remaining === 0) {
            feedbackMsg += " [Last item - now out of stock]";
            isWarning = true;
        } else if (remaining < 5) {
            feedbackMsg += ` [Only ${remaining} left in stock]`;
            isWarning = true;
        }
        
        setFeedback(feedbackMsg, isWarning);
    } catch (error) {
        setFeedback(error.message, true);
        barcodeInput.select();
    } finally {
        isProcessingScan = false;
        barcodeInput.disabled = false;
        // Restore focus AFTER disabled = false and DOM settle
        requestAnimationFrame(() => {
            barcodeInput.focus();
        });
    }
}

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
    } finally {
        // Refocus barcode input after quantity change
        setTimeout(() => barcodeInput.focus(), 50);
    }
});

checkoutForm?.addEventListener("submit", async (event) => {
    event.preventDefault();
    if (isCheckoutModalOpen) {
        return;
    }
    try {
        const formData = new FormData(checkoutForm);
        const data = await postForm("/terminal/checkout/", Object.fromEntries(formData.entries()));
        openCheckoutModal(data.receipt_number, data.receipt_url, data.thermal_receipt_url, data.a4_receipt_url);
    } catch (error) {
        setFeedback(error.message, true);
    }
});

printThermalButton?.addEventListener("click", () => {
    if (!latestThermalReceiptUrl) {
        return;
    }
    openPrintWindow(latestThermalReceiptUrl);
    continueAfterCheckout();
});

printA4Button?.addEventListener("click", () => {
    if (!latestA4ReceiptUrl) {
        return;
    }
    openPrintWindow(latestA4ReceiptUrl);
    continueAfterCheckout();
});

skipPrintButton?.addEventListener("click", () => {
    continueAfterCheckout();
});

document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && isCheckoutModalOpen) {
        continueAfterCheckout();
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

// STICKY FOCUS: Keep barcode input as primary target for scanner
// Refocus barcode input when user clicks away or blurs
barcodeInput?.addEventListener("blur", (event) => {
    if (isCheckoutModalOpen) {
        return;
    }
    // Don't refocus if user is submitting checkout
    if (event.relatedTarget?.closest("form#checkout-form")) {
        return;
    }
    // Refocus barcode input for next scan
    setTimeout(() => barcodeInput.focus(), 10);
});

// Visual indicator: Highlight barcode input when focused
barcodeInput?.addEventListener("focus", () => {
    barcodeInput.style.boxShadow = "0 0 0 3px rgba(34, 197, 94, 0.2)";
    barcodeInput.style.borderColor = "#22c55e";
});

barcodeInput?.addEventListener("blur", () => {
    barcodeInput.style.boxShadow = "";
    barcodeInput.style.borderColor = "";
});

// Tab key handling: Keep focus on barcode input during checkout
document.addEventListener("keydown", (event) => {
    // If Tab is pressed while barcode input is focused
    if (event.key === "Tab" && document.activeElement === barcodeInput) {
        // Check if user is trying to exit to checkout form
        if (checkoutForm && event.shiftKey === false) {
            // Allow Tab to move to checkout form if it's visible
            const checkoutButton = checkoutForm?.querySelector("button[type='submit']");
            if (checkoutButton) {
                // Let Tab proceed naturally to checkout
                return;
            }
        } else {
            // Shift+Tab should keep focus on barcode input
            event.preventDefault();
            barcodeInput.focus();
        }
    }
});

// Intercept clicks on quantity inputs to allow editing, then refocus barcode
document.addEventListener("click", (event) => {
    if (isCheckoutModalOpen) {
        return;
    }
    if (event.target.classList.contains("qty-input")) {
        // Allow quantity input to be edited
        // Focus will be restored after change event (see cartBody change listener)
    } else if (!event.target.closest("form#checkout-form") && !event.target.closest("button")) {
        // Click elsewhere? Refocus barcode input
        setTimeout(() => barcodeInput.focus(), 10);
    }
}, true); // Use capture phase to intercept early

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

// Initialize: Focus barcode input and display ready state
window.addEventListener("load", () => {
    barcodeInput?.focus();
    setFeedback("Ready to scan");
});
