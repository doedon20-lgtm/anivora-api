const API_BASE = "";

async function apiRequest(endpoint, options = {}) {
    try {
        const response = await fetch(API_BASE + endpoint, {
            ...options,
            headers: {
                "Content-Type": "application/json",
                ...(options.headers || {})
            }
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "API request failed");
        }

        return data;
    } catch (error) {
        console.error("AniVora API error:", error);
        return {
            success: false,
            error: error.message
        };
    }
}

async function checkAPIStatus() {
    const status = document.getElementById("apiStatus");

    if (!status) return;

    status.textContent = "Checking...";

    const data = await apiRequest("/v1/status");

    if (data.success !== false) {
        status.textContent = "● Online";
    } else {
        status.textContent = "● Offline";
    }
}

async function loadModels() {
    const modelsContainer = document.getElementById("models");

    if (!modelsContainer) return;

    const data = await apiRequest("/v1/models");

    if (!data.models) {
        modelsContainer.innerHTML = "<p>Unable to load models.</p>";
        return;
    }

    modelsContainer.innerHTML = "";

    data.models.forEach(model => {
        const item = document.createElement("div");

        item.className = "model-item";

        item.innerHTML = `
            <strong>${model.id}</strong>
            <span>${model.type || "AI Model"}</span>
        `;

        modelsContainer.appendChild(item);
    });
}

function saveAPIKey(key) {
    if (!key) return;

    sessionStorage.setItem("anivora_api_key", key);
}

function loadAPIKey() {
    const key = sessionStorage.getItem("anivora_api_key");
    const input = document.getElementById("apiKey");

    if (key && input) {
        input.value = key;
    }

    return key;
}

async function copyAPIKey() {
    const input = document.getElementById("apiKey");

    if (!input || !input.value) {
        alert("No API key available.");
        return;
    }

    await navigator.clipboard.writeText(input.value);

    alert("API key copied.");
}

function initializeDashboard() {
    loadAPIKey();
    checkAPIStatus();
    loadModels();
}

document.addEventListener("DOMContentLoaded", initializeDashboard);
