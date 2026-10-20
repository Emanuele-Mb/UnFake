import { state } from './state.js';
import { ICONS, TAG_TOOLTIPS, TONE_INTENSITY_TOOLTIP, tagTooltip, esc } from './config.js';
import { renderCharts } from './charts.js';

export const DOM = {
    get searchSection()     { return document.getElementById("search-section"); },
    get resultsSection()    { return document.getElementById("results-section"); },
    get mainSearchInput()   { return document.getElementById("main-search-input"); },
    get inlineSearchInput() { return document.getElementById("inline-search-input"); },
    get queryLabel()        { return document.getElementById("query-label"); },
    get headlinesCount()    { return document.getElementById("headlines-count"); },
    get headlinesList()     { return document.getElementById("headlines-list"); },
    get sourceFilters()     { return document.getElementById("source-filters"); },
    get sentimentFilters()  { return document.getElementById("sentiment-filters"); },
    get analysisCol()       { return document.getElementById("analysis-col"); },
    get errorMsg()          { return document.getElementById("error-message"); },
    get feedbackSection()   { return document.getElementById("feedback-section"); }
};

export function showSkeletons() {
    if (!DOM.headlinesList) return;
    DOM.headlinesList.innerHTML = `
    <div class="loading-cards">
    ${[1,2,3].map(() => `
        <div class="skeleton-card">
        <div class="skeleton-line" style="width:40%;height:12px;"></div>
        <div class="skeleton-line" style="width:90%;height:20px;margin-top:14px;"></div>
        <div class="skeleton-line" style="width:70%;height:16px;"></div>
        <div class="skeleton-line" style="width:50%;height:12px;"></div>
        </div>`).join("")}
        </div>`;
        if (DOM.analysisCol) DOM.analysisCol.style.display = "none";
}

export function buildFilters() {
    if (!DOM.sourceFilters || !DOM.sentimentFilters) return;

    const sources = [...new Set(state.allArticles.map(a => a.source))];
    const webSources = sources.filter(src => src.includes('.'));
    const traditionalSources = sources.filter(src => !src.includes('.'));

    DOM.sourceFilters.innerHTML = `<p class="filter-group-label" style="font-size:1.1rem; margin-bottom: 12px;">Sources</p>`;

    const allSelected = sources.length > 0 && state.selectedSources.length === sources.length;
    const tradSelected = traditionalSources.length > 0 && traditionalSources.every(s => state.selectedSources.includes(s));
    const webSelected = webSources.length > 0 && webSources.every(s => state.selectedSources.includes(s));

    const safeUpdate = () => {
        try {
            renderResults();
        } catch (err) {
            console.warn("Chart.js ha bloccato il render. Resetto la vista.", err);
            if (DOM.headlinesList) DOM.headlinesList.innerHTML = `<p style="padding: 20px; color: #666;">Nessuna fonte selezionata. Seleziona una fonte a sinistra.</p>`;
            if (DOM.headlinesCount) DOM.headlinesCount.textContent = "Headlines (0)";
        }
        buildFilters();
    };

    const masterTogglesContainer = document.createElement("div");
    masterTogglesContainer.style.display = "flex";
    masterTogglesContainer.style.flexDirection = "column";
    masterTogglesContainer.style.gap = "8px";
    masterTogglesContainer.style.borderBottom = "1px solid var(--border-light)";
    masterTogglesContainer.style.paddingBottom = "12px";
    masterTogglesContainer.style.marginBottom = "12px";

    const allLabel = document.createElement("label");
    allLabel.className = "filter-item";
    allLabel.style.fontWeight = "bold";
    allLabel.innerHTML = `<input type="checkbox" ${allSelected ? "checked" : ""} /><span>All Sources</span>`;
    allLabel.querySelector("input").addEventListener("change", (e) => {
        state.selectedSources = e.target.checked ? [...sources] : [];
        safeUpdate();
    });
    masterTogglesContainer.appendChild(allLabel);

    if (traditionalSources.length > 0) {
        const tradLabel = document.createElement("label");
        tradLabel.className = "filter-item";
        tradLabel.style.fontWeight = "600";
        tradLabel.style.marginLeft = "12px";
        tradLabel.innerHTML = `<input type="checkbox" ${tradSelected ? "checked" : ""} /><span style="color: #4f46e5;">All Traditional Media</span>`;
        tradLabel.querySelector("input").addEventListener("change", (e) => {
            if (e.target.checked) {
                traditionalSources.forEach(s => { if (!state.selectedSources.includes(s)) state.selectedSources.push(s); });
            } else {
                state.selectedSources = state.selectedSources.filter(s => !traditionalSources.includes(s));
            }
            safeUpdate();
        });
        masterTogglesContainer.appendChild(tradLabel);
    }

    if (webSources.length > 0) {
        const webLabel = document.createElement("label");
        webLabel.className = "filter-item";
        webLabel.style.fontWeight = "600";
        webLabel.style.marginLeft = "12px";
        webLabel.innerHTML = `<input type="checkbox" ${webSelected ? "checked" : ""} /><span style="color: #4f46e5;">All New Media</span>`;
        webLabel.querySelector("input").addEventListener("change", (e) => {
            if (e.target.checked) {
                webSources.forEach(s => { if (!state.selectedSources.includes(s)) state.selectedSources.push(s); });
            } else {
                state.selectedSources = state.selectedSources.filter(s => !webSources.includes(s));
            }
            safeUpdate();
        });
        masterTogglesContainer.appendChild(webLabel);
    }

    DOM.sourceFilters.appendChild(masterTogglesContainer);

    const columnsContainer = document.createElement("div");
    columnsContainer.style.display = "grid";
    columnsContainer.style.gridTemplateColumns = "1fr 1fr";
    columnsContainer.style.gap = "16px";
    columnsContainer.style.width = "100%";
    columnsContainer.style.minWidth = "300px";

    const renderCategoryColumn = (sourceList, categoryTitle) => {
        const col = document.createElement("div");
        col.style.display = "flex";
        col.style.flexDirection = "column";
        col.style.gap = "6px";
        col.style.minWidth = "0";

        const catHeader = document.createElement("div");
        catHeader.style.fontWeight = "bold";
        catHeader.style.fontSize = "0.70rem";
        catHeader.style.textTransform = "uppercase";
        catHeader.style.color = "#6b7280";
        catHeader.style.borderBottom = "1px solid #e5e7eb";
        catHeader.style.paddingBottom = "4px";
        catHeader.style.marginBottom = "6px";
        catHeader.textContent = categoryTitle;
        col.appendChild(catHeader);

        sourceList.forEach(src => {
            const label = document.createElement("label");
            label.className = "filter-item";
            label.style.overflow = "hidden";
            label.style.textOverflow = "ellipsis";
            label.style.whiteSpace = "nowrap";

            label.innerHTML = `<input type="checkbox" ${state.selectedSources.includes(src) ? "checked" : ""}/><span title="${src}">${src}</span>`;

            label.querySelector("input").addEventListener("change", () => {
                if (state.selectedSources.includes(src)) {
                    state.selectedSources = state.selectedSources.filter(s => s !== src);
                } else {
                    state.selectedSources.push(src);
                }
                safeUpdate();
            });

            col.appendChild(label);
        });

        return col;
    };

    columnsContainer.appendChild(renderCategoryColumn(traditionalSources, "Traditional"));
    columnsContainer.appendChild(renderCategoryColumn(webSources, "New Media"));

    DOM.sourceFilters.appendChild(columnsContainer);

    const emotionsSet = new Set();
    state.allArticles.forEach(a => {
        if (Array.isArray(a.sentiment)) {
            a.sentiment.forEach(emo => emotionsSet.add(emo));
        } else {
            emotionsSet.add(a.sentiment);
        }
    });
    const emotions = [...emotionsSet];

    DOM.sentimentFilters.innerHTML = `<p class="filter-group-label" style="font-size:1.1rem; margin-top:20px; margin-bottom: 12px;">Sentiment</p>`;

    const allEmotionsSelected = emotions.length > 0 && state.selectedSentiments.length === emotions.length;
    const selectAllEmotions = document.createElement("label");
    selectAllEmotions.className = "filter-item";
    selectAllEmotions.style.fontWeight = "bold";
    selectAllEmotions.style.borderBottom = "1px solid var(--border-light)";
    selectAllEmotions.style.paddingBottom = "12px";
    selectAllEmotions.style.marginBottom = "12px";
    selectAllEmotions.innerHTML = `<input type="checkbox" ${allEmotionsSelected ? "checked" : ""} /><span>All Sentiments</span>`;

    selectAllEmotions.querySelector("input").addEventListener("change", (e) => {
        state.selectedSentiments = e.target.checked ? [...emotions] : [];
        safeUpdate();
    });
    DOM.sentimentFilters.appendChild(selectAllEmotions);

    emotions.forEach(s => {
        const label = document.createElement("label");
        label.className = "filter-item capitalize";
        label.innerHTML = `<input type="checkbox" ${state.selectedSentiments.includes(s) ? "checked" : ""}/><span>${s.toLowerCase()}</span>`;

        label.querySelector("input").addEventListener("change", () => {
            if (state.selectedSentiments.includes(s)) {
                state.selectedSentiments = state.selectedSentiments.filter(em => em !== s);
            } else {
                state.selectedSentiments.push(s);
            }
            safeUpdate();
        });
        DOM.sentimentFilters.appendChild(label);
    });
}

export function renderResults() {
    const filtered = state.allArticles.filter(a =>
    state.selectedSources.includes(a.source) &&
    (Array.isArray(a.sentiment) ? a.sentiment.some(s => state.selectedSentiments.includes(s)) : state.selectedSentiments.includes(a.sentiment))
    );

    if (DOM.headlinesCount) DOM.headlinesCount.textContent = `Headlines (${filtered.length})`;
    if (DOM.headlinesList) DOM.headlinesList.innerHTML = "";

    if (filtered.length === 0) {
        if (DOM.headlinesList) DOM.headlinesList.innerHTML = `<p class="no-results">No articles match your selected filters.</p>`;
        if (DOM.analysisCol) DOM.analysisCol.style.display = "none";
        return;
    }

    if (DOM.analysisCol) DOM.analysisCol.style.display = "flex";
    filtered.forEach(article => DOM.headlinesList.appendChild(buildCard(article)));
    renderCharts(filtered);
    renderActors(filtered);
}

export function buildCard(article) {
    const NEGATIVE_EMOTIONS = new Set(["ANGER","ANNOYANCE","DISAPPOINTMENT","DISAPPROVAL","DISGUST","EMBARRASSMENT","FEAR","GRIEF","NERVOUSNESS","REMORSE","SADNESS"]);
    const POSITIVE_EMOTIONS = new Set(["ADMIRATION","AMUSEMENT","APPROVAL","CARING","DESIRE","EXCITEMENT","GRATITUDE","JOY","LOVE","OPTIMISM","PRIDE","RELIEF"]);

    const primarySentiment = Array.isArray(article.sentiment) ? article.sentiment[0] : article.sentiment;
    const valence = NEGATIVE_EMOTIONS.has(primarySentiment) ? "negative"
    : POSITIVE_EMOTIONS.has(primarySentiment) ? "positive"
    : "neutral";

    const badgeClass = { positive: "badge-positive", negative: "badge-negative", neutral: "badge-neutral" }[valence];
    const icon       = { positive: ICONS.thumbUp, negative: ICONS.thumbDown, neutral: ICONS.meh }[valence];
    const displaySentiment = Array.isArray(article.sentiment) ? article.sentiment.join(" / ") : article.sentiment;

    let headlineHTML = esc(article.headline);
    const headlineLower = article.headline.toLowerCase();

    article.actors.forEach(actor => {
        const actorLower = actor.name.toLowerCase();
        const actorIndex = headlineLower.indexOf(actorLower);

        if (actorIndex !== -1) {
            const actorText = article.headline.substring(actorIndex, actorIndex + actor.name.length);
            headlineHTML = headlineHTML.replace(
                new RegExp(`\\b${esc(actorText)}\\b`, 'gi'),
                                                `<mark class="headline-highlight">${esc(actorText)}</mark>`
            );
        }
    });

    const actorTags = article.actors.map(a =>
    `<span class="actor-tag">${esc(a.name)} <em class="actor-role"><span class="tooltip-wrapper" data-tooltip="${tagTooltip('agency', a.role)}">${esc(a.role)}</span></em></span>`
    ).join("");

    const focusTags = (article.focuses || article.focus || []).map(f =>
    `<span class="focus-tag"><span class="tooltip-wrapper" data-tooltip="${tagTooltip('focus', f)}">${esc(f)}</span></span>`
    ).join("");

    const urlLine = article.url ? `<div class="card-url"><a href="${esc(article.url)}" target="_blank" rel="noopener">Read original article ↗</a></div>` : "";

    const card = document.createElement("article");
    card.className = "result-card";
    card.innerHTML = `
    <div class="card-top">
    <div class="source-info">
    <div class="source-avatar">${esc(article.source.charAt(0))}</div>
    <span class="source-name">${esc(article.source)}</span>
    </div>
    <div class="sentiment-badge ${badgeClass}">${icon} ${displaySentiment}</div>
    </div>
    <h3 class="card-headline">${headlineHTML}</h3>

    <div class="analysis-tags">
    <span class="analysis-tag tag-frame">
    <span class="tooltip-wrapper" data-tooltip="${tagTooltip('frame', article.frame)}">
    Frame: ${esc(article.frame)}
    </span>
    </span>
    <span class="analysis-tag tag-genre">
    <span class="tooltip-wrapper" data-tooltip="${tagTooltip('genre', article.genre)}">
    Genre: ${esc(article.genre)}
    </span>
    </span>
    </div>

    <div class="card-meta">
    <div style="display: flex; flex-wrap: wrap; align-items: center; gap: 16px; margin-bottom: 8px; width: 100%;">
    ${article.actors.length > 0 ? `
        <div class="meta-actors" style="margin: 0; display: inline-flex; align-items: center;">
        ${ICONS.tags}
        <div class="actor-tags" style="display: flex; gap: 4px; flex-wrap: wrap; margin-left: 6px;">
        ${actorTags}
        </div>
        </div>` : ""}

        <div class="meta-biases-colored" style="display: inline-flex; align-items: center; gap: 8px; flex-wrap: wrap;">
        <span style="font-size: 12px; font-weight: bold; color: #475569;">Biases:</span>
        <div style="display: inline-flex; gap: 6px; flex-wrap: wrap;">
        ${buildBiasTags(article.biases)}
        </div>
        </div>
        </div>

        ${focusTags ? `<div class="meta-focus" style="margin-top: 4px;"><span class="meta-label">Focus:</span><div class="focus-tags">${focusTags}</div></div>` : ""}
        </div>

        ${urlLine}
        <div class="card-footer">${buildStarRating(article)}</div>
        `;
        return card;
}

export function buildStarRating(article) {
    const intensity = article.tone_intensity || 3;

    const colors = {
        1: "#10b981",
        2: "#84cc16",
        3: "#f59e0b",
        4: "#f97316",
        5: "#ef4444"
    };

    const barColor = colors[intensity] || "#f59e0b";
    const percentage = (intensity / 5) * 100;

    return `
    <div class="star-rating" style="display: flex; align-items: center; justify-content: space-between; gap: 12px;">
    <span class="rating-label tooltip-wrapper" data-tooltip="${TONE_INTENSITY_TOOLTIP}" style="white-space: nowrap;">Tone Intensity: ${intensity}/5</span>
    <div style="width: 80px; min-width: 180px; height: 8px; background-color: #e2e8f0; border-radius: 4px; overflow: hidden;">
    <div style="width: ${percentage}%; height: 100%; background-color: ${barColor}; border-radius: 4px;"></div>
    </div>
    </div>`;
}

export function buildBiasTags(biasesObj) {
    if (!biasesObj || Object.keys(biasesObj).length === 0) {
        return '<span style="font-size: 12px; color: #64748b; font-style: italic;">No bias detected</span>';
    }

    return Object.entries(biasesObj).map(([bias, score]) => {
        let intensityLabel = 'Low';
        let color = '#3b82f6';

        if (score === 2) {
            intensityLabel = 'Med';
            color = '#f59e0b';
        } else if (score === 3) {
            intensityLabel = 'High';
            color = '#ef4444';
        }

        return `
        <span style="display: inline-flex; align-items: center; padding: 4px 10px; border-radius: 12px; background-color: ${color}15; color: ${color}; font-size: 12px; font-weight: 600; border: 1px solid ${color}30;">
        ${bias} <span style="opacity: 0.7; margin-left: 4px; font-size: 10px;">(${intensityLabel})</span>
        </span>`;
    }).join('');
}

export function renderActors(articles) {
    const counts = {};
    articles.forEach(a => a.actors.forEach(actor => { const key = actor.name || actor; counts[key] = (counts[key] || 0) + 1; }));
    const top = Object.entries(counts).sort((a,b) => b[1]-a[1]).slice(0, 5);

    const listEl = document.getElementById("actors-list");
    if (listEl) {
        listEl.innerHTML = top.length > 0
        ? top.map(([actor, count]) => `<div class="actor-chip">${esc(actor)}<span class="actor-chip-count">${count}</span></div>`).join("")
        : `<p style="font-size:.85rem;color:var(--text-400)">No actors identified yet.</p>`;
    }
}

export function resetFeedbackForm() {
    state.feedbackRating = null;
    const succ = document.getElementById("feedback-success");
    const form = document.getElementById("feedback-form");
    const comm = document.getElementById("feedback-comment");

    if (succ) succ.style.display = "none";
    if (form) form.style.display = "block";
    if (comm) comm.value = "";
    document.querySelectorAll(".rating-buttons button").forEach(b => b.classList.remove("active"));
}
