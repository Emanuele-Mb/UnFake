export const ICONS = {
    search: `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="11" cy="11" r="8"/><line x1="21" y1="21" x2="16.65" y2="16.65"/></svg>`,
    filter: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/></svg>`,
    tags:   `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.59 13.41l-7.17 7.17a2 2 0 0 1-2.83 0L2 12V2h10l8.59 8.59a2 2 0 0 1 0 2.82z"/><line x1="7" y1="7" x2="7.01" y2="7"/></svg>`,
    brain:  `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.5 2a2.5 2.5 0 0 1 5 0v1.5"/><path d="M14.5 3.5a5 5 0 0 1 4.5 5v1a2 2 0 0 1 0 4v1a5 5 0 0 1-5 5h-4a5 5 0 0 1-5-5v-1a2 2 0 0 1 0-4v-1a5 5 0 0 1 4.5-5"/></svg>`,
    thumbUp:   `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3z"/><path d="M7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"/></svg>`,
    thumbDown: `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M10 15v4a3 3 0 0 0 3 3l4-9V2H5.72a2 2 0 0 0-2 1.7l-1.38 9a2 2 0 0 0 2 2.3z"/><path d="M17 2h2.67A2.31 2.31 0 0 1 22 4v7a2.31 2.31 0 0 1-2.33 2H17"/></svg>`,
    meh:       `<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="8" y1="15" x2="16" y2="15"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg>`,
};

export const TAG_TOOLTIPS = {
    frame: {
        CONFLICT:       "Presents opposing actors, forces, or interpretations in tension.",
        GAME_STRATEGY:  "Focuses on actors pursuing goals, gaining advantage, or mobilizing support",
        THEMATIC:       "Centers on a broader social/political issue or systemic concern.",
        HUMAN_INTEREST: "Tells the story through the personal experience of individuals directly affected by the issue.",
        EPISODIC:       "Presents a specific event as an isolated occurrence without connecting it to wider trends or causes.",
        OTHER:          "Headline does not fit any of the generic framing categories.",
    },
    genre: {
        INFORMATIVE:    "Straightforward reporting of facts and events with minimal interpretation.",
        INVESTIGATIVE:  "Aims to expose hidden truths or systemic issues.",
        ANALYTIC:       "Explains causes, context, or implications beyond the immediate surface facts.",
        EDITORIAL:      "Persuasive, opinion-driven piece that expresses a viewpoint, argument, or endorsement.",
        ENTERTAINMENT:  "Lifestyle, culture, soft news primarily aimed at engaging or amusing the audience.",
        OTHER:          "Headline does not clearly fit a standard category for the genre/intent.",
    },
    focus: {
        ECONOMIC:       "Framed around financial cost, trade, economic growth, or fiscal impact.",
        RESOURCES:      "Centered on natural resources, energy, land, or supply chains.",
        MORALITY:       "Raises ethical questions, values, or moral judgements.",
        FAIRNESS:       "Concerns justice, equality, rights, or distribution of outcomes.",
        LEGAL:          "Involves legislation, regulation, court decisions, or legal accountability.",
        POLICY:         "Discusses government decisions, public policy, or institutional action.",
        CRIME:          "Relates to criminal activity, law enforcement, or public order.",
        SECURITY:       "Covers threats, conflict, military action, or national security.",
        HEALTH:         "Focuses on physical or mental health, medicine, or epidemiology.",
        QOL:            "Addresses quality of life, wellbeing, housing, or social conditions.",
        CULTURAL_ID:    "Touches on cultural values, identity, religion, or social cohesion.",
        PUBLIC_OPINION: "Highlights polls, popular sentiment, or public reaction.",
        POLITICAL:      "Centers on electoral dynamics, party politics, or power relations.",
        OTHER:          "Headline does not clearly fit a standard category for focus.",
    },
    agency: {
        ACTIVE:     "Directly driving or performing the actions described in the headline.",
        PASSIVE:    "Affected by events but not the initiator of the actions.",
        MENTIONNED: "Referenced in the headline but not central to the described action.",
    },
    bias: {
        POLITICAL:      "Favors or disparages a political group, party, or ideology.",
        GENDER:         "Uses language that stereotypes or unequally represents genders.",
        CULTURAL:       "Frames an issue through a specific cultural lens, marginalizing others.",
        AGE:            "Stereotypes or dismisses individuals based on their age group.",
        RELIGION:       "Portrays a religious group or belief system in a skewed way.",
        DISABILITY:     "Uses language that stigmatizes or misrepresents people with disabilities.",
        STATEMENT:      "Presents an unverified claim or allegation as established fact.",
        OMISSION:       "Leaves out key context or facts that would change the reader's interpretation.",
        SENSATIONALISM: "Uses exaggerated or dramatic language to provoke a strong emotional reaction.",
        NEGATIVITY:     "Disproportionately emphasizes negative aspects while ignoring positives.",
        SUBJECTIVE:     "Injects personal opinion or value-laden language into what should be neutral reporting.",
        ADHOMINEM:      "Attacks a person's character rather than addressing the substance of the issue.",
        OPINION:        "Presents an editorial opinion or judgement as if it were objective reporting.",
    },
};

export const TONE_INTENSITY_TOOLTIP =
"1: Neutral, factual  ·  2: Mildly toned  ·  3: Moderately emotive  ·  4: Highly charged  ·  5: Strongly sensational";

        export function tagTooltip(type, value) {
            const map = TAG_TOOLTIPS[type] || {};
            return map[(value || "").toUpperCase()] || "No description available.";
        }

        export function esc(str) {
            return String(str || "")
            .replace(/&/g,"&amp;").replace(/</g,"&lt;")
            .replace(/>/g,"&gt;").replace(/"/g,"&quot;");
        }
