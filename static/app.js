import { state } from './state.js';
import { DOM } from './ui.js';
import { handleSearch, loadTrending } from './api.js';

function initApp() {
    // 1. Search Main
    const mainSearchBtn = document.getElementById("main-search-btn");
    if (mainSearchBtn) {
        mainSearchBtn.addEventListener("click", () => {
            const country = document.getElementById("main-country-select")?.value || "US";
            const engine  = document.getElementById("main-engine-select")?.value || "duckduckgo";
            const query   = DOM.mainSearchInput?.value || "";
            handleSearch(query, country, engine);
        });
    }

    if (DOM.mainSearchInput) {
        DOM.mainSearchInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                const country = document.getElementById("main-country-select")?.value || "US";
                const engine  = document.getElementById("main-engine-select")?.value || "duckduckgo";
                handleSearch(DOM.mainSearchInput.value, country, engine);
            }
        });
    }

    // 2. Search Inline
    const inlineSearchBtn = document.getElementById("inline-search-btn");
    if (inlineSearchBtn) {
        inlineSearchBtn.addEventListener("click", () => {
            const country = document.getElementById("inline-country-select")?.value || "US";
            const engine  = document.getElementById("inline-engine-select")?.value || "duckduckgo";
            const query   = DOM.inlineSearchInput?.value || "";
            handleSearch(query, country, engine);
        });
    }

    if (DOM.inlineSearchInput) {
        DOM.inlineSearchInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                const country = document.getElementById("inline-country-select")?.value || "US";
                const engine  = document.getElementById("inline-engine-select")?.value || "duckduckgo";
                handleSearch(DOM.inlineSearchInput.value, country, engine);
            }
        });
    }

    // 3. Feedback buttons e submit
    document.querySelectorAll(".rating-buttons button").forEach(btn => {
        btn.addEventListener("click", () => {
            state.feedbackRating = +btn.dataset.rating;
            document.querySelectorAll(".rating-buttons button").forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
        });
    });

    const feedbackForm = document.getElementById("feedback-form");
    if (feedbackForm) {
        feedbackForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            if (!state.feedbackRating) return;

            const comment  = document.getElementById("feedback-comment")?.value || "";
            const language = navigator.language.split("-")[0] || "en";

            try {
                await fetch("/feedback", {
                    method:  "POST",
                    headers: { "Content-Type": "application/json" },
                    body:    JSON.stringify({ event: state.currentQuery, rating: state.feedbackRating, comment, language }),
                });
                document.getElementById("feedback-form").style.display    = "none";
                document.getElementById("feedback-success").style.display = "block";
            } catch(err) { console.error("Global feedback error:", err); }
        });
    }

    // 4. Carica Trending Topic
    loadTrending();
}

if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", initApp);
} else {
    initApp();
}
