import { state } from './state.js';
import { DOM, showSkeletons, buildFilters, renderResults, resetFeedbackForm } from './ui.js';
import { esc } from './config.js';

export async function handleSearch(query, country = "US", engine = "duckduckgo") {
    if (!query.trim()) return;

    const mainEngine = document.getElementById("main-engine-select");
    const inlineEngine = document.getElementById("inline-engine-select");
    if (mainEngine) mainEngine.value = engine;
    if (inlineEngine) inlineEngine.value = engine;

    state.currentQuery   = query;
    state.feedbackRating = null;

    if (DOM.searchSection) DOM.searchSection.style.display  = "none";
    if (DOM.resultsSection) DOM.resultsSection.style.display = "block";
    if (DOM.queryLabel) DOM.queryLabel.textContent       = `"${query}"`;
    if (DOM.inlineSearchInput) DOM.inlineSearchInput.value = query;

    const inlineCountry = document.getElementById("inline-country-select");
    const mainCountry = document.getElementById("main-country-select");
    if (inlineCountry) inlineCountry.value = country;
    if (mainCountry) mainCountry.value = country;

    if (DOM.errorMsg) DOM.errorMsg.style.display = "none";
    if (DOM.feedbackSection) DOM.feedbackSection.style.display = "none";

    showSkeletons();

    try {
        const res = await fetch("/search", {
            method:  "POST",
            headers: { "Content-Type": "application/json" },
            body:    JSON.stringify({ event: query, country: country, engine: engine }),
        });

        if (!res.ok) throw new Error("Search failed");

        const data = await res.json();

        state.allArticles = (data.articles || []).map((a, i) => ({
            id:             a.url || String(i),
                                                                 headline:       a.title || a.headline || "No Title",
                                                                 source:         a.source || "Unknown Source",
                                                                 sentiment:      Array.isArray(a.sentiment) ? a.sentiment : [a.sentiment || "NEUTRAL"],
                                                                 actors:         a.actors    || [],
                                                                 frame:          a.frame     || "OTHER",
                                                                 biases:         a.biases    || {},
                                                                 focuses:        a.focuses || a.focus || [],
                                                                 genre:          a.genre     || "OTHER",
                                                                 tone_intensity: a.tone_intensity || 3,
                                                                 firstWord:      a.firstWord || a.key_phrase || "",
                                                                 url:            a.url       || null,
                                                                 description:    a.description || "",
        }));

        state.selectedSources = [...new Set(state.allArticles.map(a => a.source))];
        const emotionsSet = new Set();
        state.allArticles.forEach(a => {
            if (Array.isArray(a.sentiment)) {
                a.sentiment.forEach(emo => emotionsSet.add(emo));
            } else {
                emotionsSet.add(a.sentiment);
            }
        });
        state.selectedSentiments = [...emotionsSet];

        buildFilters();
        renderResults();
        if (DOM.feedbackSection) DOM.feedbackSection.style.display = "block";
        resetFeedbackForm();

    } catch (err) {
        console.error("Search Error:", err);
        if (DOM.errorMsg) {
            DOM.errorMsg.textContent = "An error occurred during the search. Please try again.";
            DOM.errorMsg.style.display = "block";
        }
        if (DOM.headlinesList) DOM.headlinesList.innerHTML = "";
        if (DOM.analysisCol) DOM.analysisCol.style.display = "none";
    }
}

export async function loadTrending() {
    try {
        const res = await fetch("/api/analytics-data");
        if (!res.ok) return;
        const data = await res.json();

        const stats  = data.topic_stats || [];
        const sorted = [...stats].sort((a, b) => (b.count || 0) - (a.count || 0)).slice(0, 6);
        const list   = document.getElementById("trending-list");
        if (!list || sorted.length === 0) return;

        list.innerHTML = "";
        sorted.forEach(t => {
            const chip = document.createElement("button");
            chip.className   = "trending-chip";
            chip.textContent = t.event_query;
            chip.addEventListener("click", () => handleSearch(t.event_query));
            list.appendChild(chip);
        });
    } catch(e) {
        // Analytics non disponibili
    }
}
