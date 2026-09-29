const API_BASE = "";

/* ================================
   SAFE JSON API REQUEST
================================ */

async function apiRequest(endpoint, options = {}) {
    try {
        const response = await fetch(API_BASE + endpoint, {
            ...options,
            headers: {
                "Accept": "application/json",
                "Content-Type": "application/json",
                ...(options.headers || {})
            }
        });

        // Safely read the response.
        const rawText = await response.text();

        let data = null;

        try {
            data = rawText ? JSON.parse(rawText) : {};
        } catch {
            throw new Error(
                `Server returned invalid JSON (HTTP ${response.status}).`
            );
        }

        if (!response.ok) {
            throw new Error(
                data?.error ||
                data?.message ||
                `API request failed (HTTP ${response.status}).`
            );
        }

        return {
            success: true,
            data
        };

    } catch (error) {
        console.error("AniVora API Error:", error);

        return {
            success: false,
            error: error?.message || "Unable to connect to AniVora API."
        };
    }
}


/* ================================
   STATUS LOADING
================================ */

function setStatusLoading() {
    const status = document.getElementById("apiStatus");

    if (!status) return;

    status.textContent = "● Checking API...";
    status.classList.remove("online", "offline");
    status.classList.add("loading");
}


function setStatusOnline() {
    const status = document.getElementById("apiStatus");

    if (!status) return;

    status.textContent = "● Online";
    status.classList.remove("loading", "offline");
    status.classList.add("online");
}


function setStatusOffline(message = "● Offline") {
    const status = document.getElementById("apiStatus");

    if (!status) return;

    status.textContent = message;
    status.classList.remove("loading", "online");
    status.classList.add("offline");
}


/* ================================
   CHECK API STATUS
================================ */

async function checkAPIStatus() {
    setStatusLoading();

    const result = await apiRequest("/v1/status");

    if (!result.success) {
        setStatusOffline("● Offline");
        showDashboardError(result.error);
        return false;
    }

    setStatusOnline();
    return true;
}


/* ================================
   MODEL LOADING
================================ */

function showModelsLoading() {
    const container = document.getElementById("models");

    if (!container) return;

    container.innerHTML = `
        <div class="dashboard-loading">
            <span class="loading-spinner"></span>
            <span>Loading AniVora models...</span>
        </div>
    `;
}


function showModelsError(message) {
    const container = document.getElementById("models");

    if (!container) return;

    container.innerHTML = `
        <div class="dashboard-error">
            <strong>Unable to load models</strong>
            <p>${escapeHTML(message)}</p>
            <button onclick="loadModels()">Retry</button>
        </div>
    `;
}


async function loadModels() {
    const container = document.getElementById("models");

    if (!container) return;

    showModelsLoading();

    const result = await apiRequest("/v1/models");

    if (!result.success) {
        showModelsError(result.error);
        return;
    }

    const models = result.data?.models;

    if (!Array.isArray(models)) {
        showModelsError("The API returned an invalid models response.");
        return;
    }

    if (models.length === 0) {
        container.innerHTML = `
            <div class="dashboard-empty">
                No models are currently available.
            </div>
        `;
        return;
    }

    container.innerHTML = "";

    models.forEach(model => {
        const item = document.createElement("div");

        item.className = "model-item";

        const modelId =
            typeof model === "string"
                ? model
                : model?.id || "Unknown model";

        const modelType =
            typeof model === "object"
                ? model?.type || "AI Model"
                : "AI Model";

        item.innerHTML = `
            <strong>${escapeHTML(modelId)}</strong>
            <span>${escapeHTML(modelType)}</span>
        `;

        container.appendChild(item);
    });
}


/* ================================
   API KEY
================================ */

function saveAPIKey(key) {
    if (!key || typeof key !== "string") {
        return false;
    }

    try {
        sessionStorage.setItem("anivora_api_key", key);
        return true;
    } catch (error) {
        console.error("Could not save API key:", error);
        return false;
    }
}


function loadAPIKey() {
    const input = document.getElementById("apiKey");

    if (!input) return null;

    try {
        const key = sessionStorage.getItem("anivora_api_key");

        if (key) {
            input.value = key;
        }

        return key;
    } catch (error) {
        console.error("Could not load API key:", error);
        return null;
    }
}


async function copyAPIKey() {
    const input = document.getElementById("apiKey");

    if (!input || !input.value) {
        showDashboardError("There is no API key to copy.");
        return;
    }

    try {
        await navigator.clipboard.writeText(input.value);

        showDashboardMessage("API key copied successfully.");

    } catch {
        // Fallback for browsers where clipboard API is unavailable.
        input.select();
        input.setSelectionRange(0, 99999);

        try {
            document.execCommand("copy");
            showDashboardMessage("API key copied successfully.");
        } catch {
            showDashboardError(
                "Could not copy the API key. Please copy it manually."
            );
        }
    }
}


/* ================================
   DASHBOARD MESSAGES
================================ */

function showDashboardMessage(message) {
    let box = document.getElementById("dashboardMessage");

    if (!box) {
        box = document.createElement("div");
        box.id = "dashboardMessage";

        document.body.prepend(box);
    }

    box.textContent = message;
    box.className = "dashboard-message";

    setTimeout(() => {
        box.remove();
    }, 4000);
}


function showDashboardError(message) {
    let box = document.getElementById("dashboardError");

    if (!box) {
        box = document.createElement("div");
        box.id = "dashboardError";

        document.body.prepend(box);
    }

    box.innerHTML = `
        <strong>AniVora API Error</strong>
        <span>${escapeHTML(message)}</span>
        <button onclick="this.parentElement.remove()">Dismiss</button>
    `;

    box.className = "dashboard-error-banner";
}


/* ================================
   SAFE HTML OUTPUT
================================ */

function escapeHTML(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}


/* ================================
   INITIALIZE DASHBOARD
================================ */

async function initializeDashboard() {
    loadAPIKey();

    // Check API first.
    const apiOnline = await checkAPIStatus();

    // Only load models after API status succeeds.
    if (apiOnline) {
        await loadModels();
    }
}


/* ================================
   START
================================ */

document.addEventListener(
    "DOMContentLoaded",
    initializeDashboard
);
