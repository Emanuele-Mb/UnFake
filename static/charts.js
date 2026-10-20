import { state } from './state.js';

export function renderCharts(articles) {
    const primaryEmotionCounts = {};
    const secondaryEmotionCounts = {};

    articles.forEach(a => {
        let primary = "Unknown";
        let secondary = null;

        if (Array.isArray(a.sentiment)) {
            primary = (a.sentiment[0] || "Unknown").trim();
            if (a.sentiment.length > 1) {
                secondary = a.sentiment[1].trim();
            }
        } else {
            primary = (a.sentiment || "Unknown").trim();
        }

        primaryEmotionCounts[primary] = (primaryEmotionCounts[primary] || 0) + 1;
        if (secondary) {
            secondaryEmotionCounts[secondary] = (secondaryEmotionCounts[secondary] || 0) + 1;
        }
    });

    const emotionColorPalette = [
        "#4f46e5", "#10b981", "#f59e0b", "#f43f5e", "#64748b",
        "#8b5cf6", "#06b6d4", "#ec4899", "#84cc16", "#f97316"
    ];

    const primaryLabels = Object.keys(primaryEmotionCounts);
    const primaryColors = primaryLabels.map((_, i) => emotionColorPalette[i % emotionColorPalette.length]);

    if (state.pieChart) state.pieChart.destroy();
    state.pieChart = new Chart(document.getElementById("pie-chart"), {
        type: "doughnut",
        data: {
            labels: primaryLabels,
            datasets: [{ data: Object.values(primaryEmotionCounts), backgroundColor: primaryColors, borderWidth: 0, hoverOffset: 6 }],
        },
        options: {
            responsive: true, maintainAspectRatio: false, cutout: "65%",
            plugins: {
                legend: {
                    position: "bottom", align: "start",
                    labels: { usePointStyle: true, pointStyle: "circle", padding: 16, font: { family: "'DM Sans'", size: 12 }, color: "#717182" },
                },
            },
        },
    });

    const secondaryLabels = Object.keys(secondaryEmotionCounts);
    const secondaryColors = secondaryLabels.map((_, i) => emotionColorPalette[(i + 3) % emotionColorPalette.length]);

    if (state.secondaryEmotionChart) state.secondaryEmotionChart.destroy();

    const secCanvas = document.getElementById("secondary-emotion-chart");
    if (secCanvas && secondaryLabels.length > 0) {
        state.secondaryEmotionChart = new Chart(secCanvas, {
            type: "doughnut",
            data: {
                labels: secondaryLabels,
                datasets: [{ data: Object.values(secondaryEmotionCounts), backgroundColor: secondaryColors, borderWidth: 0, hoverOffset: 6 }],
            },
            options: {
                responsive: true, maintainAspectRatio: false, cutout: "65%",
                plugins: {
                    legend: {
                        position: "bottom", align: "start",
                        labels: { usePointStyle: true, pointStyle: "circle", padding: 16, font: { family: "'DM Sans'", size: 12 }, color: "#717182" },
                    },
                },
            },
        });
    }

    const genreCounts = {};
    articles.forEach(a => {
        const g = (a.genre || "Unknown").trim();
        genreCounts[g] = (genreCounts[g] || 0) + 1;
    });

    const genreColorPalette = [
        "#8b5cf6", "#06b6d4", "#ec4899", "#84cc16", "#f97316",
        "#4f46e5", "#10b981", "#f59e0b", "#f43f5e", "#64748b"
    ];
    const genreLabels = Object.keys(genreCounts);
    const genreColors = genreLabels.map((_, i) => genreColorPalette[i % genreColorPalette.length]);

    if (state.genreChart) state.genreChart.destroy();
    state.genreChart = new Chart(document.getElementById("genre-chart"), {
        type: "doughnut",
        data: {
            labels: genreLabels,
            datasets: [{ data: Object.values(genreCounts), backgroundColor: genreColors, borderWidth: 0, hoverOffset: 6 }],
        },
        options: {
            responsive: true, maintainAspectRatio: false, cutout: "65%",
            plugins: {
                legend: {
                    position: "bottom", align: "start",
                    labels: { usePointStyle: true, pointStyle: "circle", padding: 16, font: { family: "'DM Sans'", size: 12 }, color: "#717182" },
                },
            },
        },
    });

    const intensityCounts = { 1: 0, 2: 0, 3: 0, 4: 0, 5: 0 };

    articles.forEach(a => {
        const intensity = a.tone_intensity || 3;
        if (intensityCounts[intensity] !== undefined) {
            intensityCounts[intensity]++;
        }
    });

    const intensityColors = ["#10b981", "#84cc16", "#f59e0b", "#f97316", "#ef4444"];

    if (state.barChart) state.barChart.destroy();
    const barCanvas = document.getElementById("bar-chart");
    if (barCanvas) {
        state.barChart = new Chart(barCanvas, {
            type: "bar",
            data: {
                labels: ["1", "2", "3", "4", "5"],
                datasets: [{
                    label: "Articoli",
                    data: [
                        intensityCounts[1],
                        intensityCounts[2],
                        intensityCounts[3],
                        intensityCounts[4],
                        intensityCounts[5]
                    ],
                    backgroundColor: intensityColors,
                    borderRadius: 5,
                    barThickness: 28
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: {
                        grid: { display: false },
                        border: { display: false },
                        ticks: { font: { family: "'DM Sans'", size: 11 }, color: "#717182" }
                    },
                    y: {
                        grid: { color: "#f0f0f2" },
                        border: { display: false },
                        ticks: { precision: 0, font: { family: "'DM Sans'", size: 11 }, color: "#717182" }
                    },
                },
            },
        });
    }
}
