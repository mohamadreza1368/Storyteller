// Application State
let currentNovelId = null;
let currentNovel = null;
let currentEpisodeNumber = null;
let currentEpisodeData = null;
let readerFontSize = 1.25;
let progressPollTimer = null;

// Authentication & Admin State
let currentUser = null;
let authToken = localStorage.getItem("st_auth_token") || null;
let adminUsersCache = [];

// Authenticated Fetch Helper
async function fetchWithAuth(url, options = {}) {
    options.headers = options.headers || {};
    if (!(options.headers instanceof Headers)) {
        if (!options.headers["Content-Type"] && !(options.body instanceof FormData)) {
            options.headers["Content-Type"] = "application/json";
        }
        if (authToken) {
            options.headers["Authorization"] = `Bearer ${authToken}`;
        }
    } else {
        if (authToken) {
            options.headers.set("Authorization", `Bearer ${authToken}`);
        }
    }
    const res = await fetch(url, options);
    if (res.status === 401 && !url.includes("/api/auth/login") && !url.includes("/api/auth/register")) {
        if (authToken) {
            authToken = null;
            currentUser = null;
            localStorage.removeItem("st_auth_token");
            updateUserNavUI();
            showToast("Session expired. Please sign in again.", "info");
        }
    }
    return res;
}

// Modern SVG Icons Dictionary
const ICONS = {
    book: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M4 19.5v-15A2.5 2.5 0 0 1 6.5 2H20v20H6.5a2.5 2.5 0 0 1-2.5-2.5Z"/><path d="M6 6h10"/><path d="M6 10h10"/></svg>`,
    quill: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>`,
    clock: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>`,
    target: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="6"/><circle cx="12" cy="12" r="2"/></svg>`,
    seedling: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 10a6 6 0 0 0-6-6H3v3a6 6 0 0 0 6 6h3"/><path d="M12 14a6 6 0 0 1 6-6h3v3a6 6 0 0 1-6 6h-3"/><line x1="12" y1="10" x2="12" y2="22"/></svg>`,
    lock: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>`,
    mapPin: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg>`,
    lightbulb: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 18h6"/><path d="M10 22h4"/><path d="M15.09 14c.18-.98.65-1.74 1.41-2.5A4.65 4.65 0 0 0 18 8 6 6 0 0 0 6 8c0 1 .23 2.23 1.5 3.5.76.76 1.23 1.52 1.41 2.5"/></svg>`,
    user: `<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21v-2a4 4 0 0 0-4-4H9a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`,
    check: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>`,
    alert: `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`,
    theater: `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="23 7 16 12 23 17 23 7"/><rect x="1" y="5" width="15" height="14" rx="2" ry="2"/></svg>`,
    trash: `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path></svg>`
};

// Genre Atmospheric Cover Images (Bespoke AI-generated literary artworks)
const GENRE_COVERS = {
    "Mystery & Crime": "/static/assets/covers/blackwood.jpg",
    "Romance": "/static/assets/covers/autumn_paris.jpg",
    "Sci-Fi": "/static/assets/covers/protocol_zero.jpg",
    "Fantasy": "/static/assets/covers/fantasy.jpg",
    "Historical": "/static/assets/covers/historical.jpg",
    "Horror": "/static/assets/covers/horror.jpg",
    "Drama": "/static/assets/covers/autumn_paris.jpg",
    "Adventure": "/static/assets/covers/fantasy.jpg",
    "default": "/static/assets/covers/blackwood.jpg"
};

// Character Avatars by identity & persona
const AVATAR_PORTRAITS = {
    julian: "/static/assets/avatars/julian.jpg",
    clara: "/static/assets/avatars/clara.jpg",
    scholar: "/static/assets/avatars/scholar.jpg",
    cyber: "/static/assets/avatars/cyber.jpg"
};

function getCharacterAvatar(name = "", gender = "Male", role = "") {
    const combined = `${name} ${role}`.toLowerCase();
    if (combined.includes("clara") || combined.includes("sterling") || combined.includes("journalist") || combined.includes("reporter") || gender.toLowerCase() === "female") {
        return AVATAR_PORTRAITS.clara;
    }
    if (combined.includes("cyber") || combined.includes("hacker") || combined.includes("operative") || combined.includes("voss") || combined.includes("rebel")) {
        return AVATAR_PORTRAITS.cyber;
    }
    if (combined.includes("scholar") || combined.includes("professor") || combined.includes("doctor") || combined.includes("thorne") || combined.includes("elder") || combined.includes("mentor") || combined.includes("historian")) {
        return AVATAR_PORTRAITS.scholar;
    }
    return AVATAR_PORTRAITS.julian;
}

function getCoverForNovel(genre = "") {
    for (const key of Object.keys(GENRE_COVERS)) {
        if (genre.toLowerCase().includes(key.toLowerCase())) {
            return GENRE_COVERS[key];
        }
    }
    return GENRE_COVERS.default;
}

// Toast System
function showToast(message, type = "info") {
    const container = document.getElementById("toastContainer");
    if (!container) return;
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    const iconSvg = type === "success" ? ICONS.check : (type === "error" ? ICONS.alert : ICONS.quill);
    toast.innerHTML = `
        <span style="display: flex; align-items: center; color: ${type === 'success' ? 'var(--success)' : (type === 'error' ? 'var(--danger)' : 'var(--accent)')};">${iconSvg}</span>
        <span>${message}</span>
    `;
    container.appendChild(toast);
    setTimeout(() => {
        toast.style.opacity = "0";
        toast.style.transform = "translateY(10px)";
        toast.style.transition = "all 0.3s ease";
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

const ENUMS = {
    genres: ["Drama", "Mystery & Crime", "Romance", "Historical", "Fantasy", "Sci-Fi", "Horror", "Adventure", "Social Drama", "Magical Realism"],
    proseStyles: ["Literary & Elegant", "Clear & Fluent", "Poetic & Vivid", "Crisp & Minimalist", "Witty & Satirical", "Cold & Journalistic", "Stream of Consciousness", "Epic & Grand"],
    themes: ["Love & Sacrifice", "Power & Corruption", "Identity & Belonging", "Forgiveness & Redemption", "Revenge & Justice", "Freedom & Autonomy", "Loneliness & Connection", "Truth & Deceit", "Death & Legacy", "War & Humanity"],
    tones: ["Dark & Gritty", "Hopeful & Inspiring", "Bittersweet", "Tense & Suspenseful", "Humorous & Witty", "Nostalgic & Melancholic", "Cold & Objective"],
    perspectives: ["Third-Person Limited", "First-Person", "Omniscient"],
    endings: ["Surprising Twist", "Triumphant & Uplifting", "Tragic & Somber", "Open-Ended & Thought-Provoking"]
};

// Initialize
document.addEventListener("DOMContentLoaded", async () => {
    populateEnums();
    await checkAuthStatus();
    await checkSystemInfo();
    await loadLibrary();
    if (document.querySelectorAll(".char-card").length === 0) {
        addCharacterCard("Julian Vance", "Main", "Male", "Archival Conservator", "Scarred Cynic");
        addCharacterCard("Clara Sterling", "Main", "Female", "Investigative Journalist", "Passionate Idealist");
    }

    // Close user dropdown when clicking outside
    window.addEventListener("click", (e) => {
        const userSection = document.getElementById("navUserSection");
        const dropdown = document.getElementById("userDropdownMenu");
        if (dropdown && userSection && !userSection.contains(e.target)) {
            dropdown.classList.remove("show");
        }
    });
});

function populateEnums() {
    const fill = (id, list) => {
        const el = document.getElementById(id);
        if (el) {
            el.innerHTML = list.map(item => `<option value="${item}">${item}</option>`).join("");
        }
    };
    fill("wizGenre", ENUMS.genres);
    fill("wizProseStyle", ENUMS.proseStyles);
    fill("wizTheme", ENUMS.themes);
    fill("wizTone", ENUMS.tones);
    fill("wizPerspective", ENUMS.perspectives);
    fill("wizEnding", ENUMS.endings);
}

// Navigation
function navigateTo(viewName) {
    if (viewName === "admin") {
        if (!currentUser || currentUser.role !== "admin") {
            showToast("Administrator privileges required.", "error");
            openAuthModal("login");
            return;
        }
    }

    document.getElementById("viewLibrary").style.display = (viewName === "library") ? "block" : "none";
    document.getElementById("viewWizard").style.display = (viewName === "wizard") ? "block" : "none";
    document.getElementById("viewNovel").style.display = (viewName === "novel") ? "block" : "none";
    document.getElementById("viewReader").style.display = (viewName === "reader") ? "block" : "none";
    const adminEl = document.getElementById("viewAdmin");
    if (adminEl) adminEl.style.display = (viewName === "admin") ? "block" : "none";

    if (viewName === "library") {
        stopProgressPolling();
        loadLibrary();
    } else if (viewName === "admin") {
        stopProgressPolling();
        loadAdminDashboard();
    }
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

// System Info
async function checkSystemInfo() {
    try {
        const res = await fetch("/api/system/info");
        const data = await res.json();
        const banner = document.getElementById("demoBanner");
        if (data.demo_mode) {
            banner.style.display = "flex";
            document.getElementById("demoMessage").innerText = data.demo_message;
        } else {
            banner.style.display = "none";
        }
    } catch (e) {
        console.error("System info error:", e);
    }
}

// Theme Toggle
function toggleTheme() {
    const current = document.documentElement.getAttribute("data-theme");
    document.documentElement.setAttribute("data-theme", current === "dark" ? "light" : "dark");
}

function setReaderTheme(themeName) {
    if (themeName === "sepia") {
        document.documentElement.setAttribute("data-reader-theme", "sepia");
    } else {
        document.documentElement.removeAttribute("data-reader-theme");
        document.documentElement.setAttribute("data-theme", themeName);
    }
}

// Load Library with Visual Cover Art
async function loadLibrary() {
    const grid = document.getElementById("novelsGrid");
    grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: var(--text-tertiary); padding: 50px;">Preparing Author's Desk…</div>`;
    
    try {
        const res = await fetchWithAuth("/api/novels");
        const novels = await res.json();
        
        if (novels.length === 0) {
            grid.innerHTML = `
                <div style="grid-column: 1/-1; text-align: center; padding: 48px 24px; background: var(--bg-surface); border-radius: var(--radius-lg); border: 1px solid var(--border-subtle); overflow: hidden;">
                    <div style="max-width: 640px; margin: 0 auto;">
                        <div style="border-radius: var(--radius-md); overflow: hidden; margin-bottom: 24px; box-shadow: var(--shadow-lg); border: 1px solid var(--border-strong);">
                            <img src="/static/assets/illustrations/studio_desk.jpg" alt="Author's Desk Sanctuary" style="width: 100%; height: 260px; object-fit: cover; display: block;">
                        </div>
                        <h3 style="font-weight: 800; font-size: 1.55rem; margin-bottom: 8px;">The Author's Desk is Ready</h3>
                        <p style="color: var(--text-secondary); max-width: 480px; margin: 0 auto 24px;">Launch instantly using our curated visual presets or craft your own original narrative from scratch.</p>
                        <button class="btn btn-primary btn-lg" onclick="startNewNovel()">
                            ${ICONS.quill}
                            Create Your First Novel
                        </button>
                    </div>
                </div>
            `;
            return;
        }

        grid.innerHTML = novels.map(n => {
            const coverUrl = getCoverForNovel(n.genre);
            const statusClass = n.status === 'Completed' ? 'badge-completed' : (n.status === 'Writing Episode' ? 'badge-writing' : 'badge-ready');
            const authorTag = n.owner_name ? `<span style="font-size: 0.76rem; font-weight: 600; color: rgba(255,255,255,0.9); background: rgba(0,0,0,0.4); padding: 2px 7px; border-radius: 4px; backdrop-filter: blur(4px);">By ${n.owner_name}</span>` : '';
            return `
            <div class="novel-card" onclick="openNovel('${n.novel_id}')">
                <div class="novel-card-cover">
                    <img src="${coverUrl}" alt="${n.title}" loading="lazy">
                    <div class="novel-card-cover-overlay">
                        <span class="badge ${statusClass}">
                            ${n.status}
                        </span>
                        <div style="display: flex; gap: 4px; align-items: center;">
                            ${authorTag}
                            <span style="font-size: 0.78rem; font-weight: 700; color: #FFFFFF; background: rgba(0,0,0,0.45); padding: 3px 8px; border-radius: 4px; backdrop-filter: blur(4px);">${n.genre}</span>
                        </div>
                    </div>
                </div>
                <div class="novel-card-body">
                    <div>
                        <h3 style="font-size: 1.3rem; font-weight: 800; margin-bottom: 8px; color: var(--text-primary); line-height: 1.4;">${n.title}</h3>
                        <p style="color: var(--text-secondary); font-size: 0.9rem; line-height: 1.6; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;">
                            ${n.premise || 'No initial premise provided'}
                        </p>
                    </div>
                    <div style="margin-top: 20px; padding-top: 14px; border-top: 1px solid var(--border-subtle); display: flex; justify-content: space-between; font-size: 0.85rem; color: var(--text-tertiary); font-weight: 600;">
                        <span style="display: flex; align-items: center; gap: 6px;">${ICONS.book} ${n.written_episodes} of ${n.total_episodes} Chapters</span>
                        <span style="display: flex; align-items: center; gap: 6px;">${ICONS.quill} ${n.total_words ? n.total_words.toLocaleString() + ' words' : 'Draft'}</span>
                    </div>
                </div>
            </div>
            `;
        }).join("");

    } catch (e) {
        grid.innerHTML = `<div style="grid-column: 1/-1; color: var(--danger); text-align: center;">Error connecting to server: ${e.message}</div>`;
    }
}

// Wizard Logic
function startNewNovel() {
    setWizardStep(1);
    navigateTo('wizard');
}

function setWizardStep(stepNum) {
    for (let i = 1; i <= 4; i++) {
        document.getElementById(`wizardStep${i}`).style.display = (i === stepNum) ? "block" : "none";
        const tab = document.getElementById(`tabNav${i}`);
        tab.className = (i === stepNum) ? "tab-btn active" : "tab-btn";
    }
}

// Apply Preset
async function applyPreset(presetName) {
    try {
        const res = await fetch("/api/novels/magic-blueprint", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt: presetName })
        });
        const bp = await res.json();
        fillWizardWithBlueprint(bp);
        setWizardStep(1);
        showToast(`Preset loaded into the wizard!`, "success");
    } catch (e) {
        showToast("Error loading preset: " + e.message, "error");
    }
}

// Magic AI Auto-Fill
async function triggerMagicAutoFill() {
    const prompt = document.getElementById("magicPromptInput").value.trim();
    if (!prompt) {
        showToast("Please provide a prompt or premise in the input box.", "error");
        return;
    }

    const btn = event.target;
    const oldText = btn.innerHTML;
    btn.innerHTML = `<span>Expanding...</span>`;
    btn.disabled = true;

    try {
        const res = await fetch("/api/novels/magic-blueprint", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt: prompt })
        });
        const bp = await res.json();
        fillWizardWithBlueprint(bp);
        showToast("AI synthesized characters, world rules, and plotlines!", "success");
        setWizardStep(1);
    } catch (e) {
        showToast("Error: " + e.message, "error");
    } finally {
        btn.innerHTML = oldText;
        btn.disabled = false;
    }
}

function fillWizardWithBlueprint(bp) {
    if (bp.title) document.getElementById("wizTitle").value = bp.title;
    if (bp.premise) document.getElementById("wizPremise").value = bp.premise;
    if (bp.genre) document.getElementById("wizGenre").value = bp.genre;
    if (bp.prose_style) document.getElementById("wizProseStyle").value = bp.prose_style;
    if (bp.theme) document.getElementById("wizTheme").value = bp.theme;
    if (bp.tone) document.getElementById("wizTone").value = bp.tone;
    if (bp.city) document.getElementById("wizCity").value = bp.city;
    if (bp.era) document.getElementById("wizEra").value = bp.era;
    if (bp.world_rules) document.getElementById("wizRules").value = bp.world_rules.join("\n");

    const locContainer = document.getElementById("wizLocationsList");
    locContainer.innerHTML = "";
    (bp.locations || []).forEach(l => {
        addLocationRow(l.name, l.description);
    });

    const charContainer = document.getElementById("wizCharactersList");
    charContainer.innerHTML = "";
    (bp.characters || []).forEach(c => {
        addCharacterCard(c.name, c.role, c.gender, c.occupation, c.persona);
    });
}

function addLocationRow(name = "", desc = "") {
    const container = document.getElementById("wizLocationsList");
    const div = document.createElement("div");
    div.style = "display: flex; gap: 10px; margin-bottom: 10px;";
    div.innerHTML = `
        <input type="text" class="form-input loc-name" placeholder="Location Name" value="${name}">
        <input type="text" class="form-input loc-desc" placeholder="Sensory details and atmosphere" value="${desc}">
    `;
    container.appendChild(div);
}

function addCharacterCard(name = "", role = "Main", gender = "Male", occupation = "", archetype = "") {
    const container = document.getElementById("wizCharactersList");
    const div = document.createElement("div");
    div.className = "card char-card";
    div.style = "padding: 18px; margin-bottom: 16px; background: var(--bg-surface-subtle); border: 1px solid var(--border-subtle);";
    div.innerHTML = `
        <div style="display: grid; grid-template-columns: 2fr 1fr 1fr; gap: 10px; margin-bottom: 10px;">
            <input type="text" class="form-input char-name" placeholder="Character Name" value="${name}">
            <select class="form-select char-role">
                <option value="Main" ${role.toLowerCase() === 'main' ? 'selected' : ''}>Main Character</option>
                <option value="Supporting" ${role.toLowerCase() === 'supporting' ? 'selected' : ''}>Supporting Character</option>
            </select>
            <select class="form-select char-gender">
                <option value="Male" ${gender.toLowerCase() === 'male' ? 'selected' : ''}>Male</option>
                <option value="Female" ${gender.toLowerCase() === 'female' ? 'selected' : ''}>Female</option>
                <option value="Non-binary" ${gender.toLowerCase() === 'non-binary' ? 'selected' : ''}>Non-binary</option>
            </select>
        </div>
        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px;">
            <input type="text" class="form-input char-occupation" placeholder="Occupation or Social Role" value="${occupation}">
            <input type="text" class="form-input char-archetype" placeholder="Archetype (e.g. Scarred Cynic)" value="${archetype}">
        </div>
    `;
    container.appendChild(div);
}

async function submitCreateNovel() {
    const title = document.getElementById("wizTitle").value.trim();
    const premise = document.getElementById("wizPremise").value.trim();
    const genre = document.getElementById("wizGenre").value;
    const prose_style = document.getElementById("wizProseStyle").value;
    const theme = document.getElementById("wizTheme").value;
    const tone = document.getElementById("wizTone").value;
    const city = document.getElementById("wizCity").value.trim();
    const era = document.getElementById("wizEra").value.trim();
    const rulesText = document.getElementById("wizRules").value.trim();
    const rules = rulesText ? rulesText.split("\n").map(r => r.trim()).filter(Boolean) : [];
    
    const locNames = document.querySelectorAll(".loc-name");
    const locDescs = document.querySelectorAll(".loc-desc");
    const locations = [];
    locNames.forEach((input, idx) => {
        if (input.value.trim()) {
            locations.push({
                name: input.value.trim(),
                description: locDescs[idx]?.value.trim() || ""
            });
        }
    });

    const charCards = document.querySelectorAll(".char-card");
    const characters = [];
    charCards.forEach(card => {
        const name = card.querySelector(".char-name")?.value.trim();
        if (name) {
            characters.push({
                name: name,
                role: card.querySelector(".char-role")?.value || "Main",
                gender: card.querySelector(".char-gender")?.value || "Male",
                occupation: card.querySelector(".char-occupation")?.value.trim() || "",
                persona: card.querySelector(".char-archetype")?.value.trim() || ""
            });
        }
    });

    const total_episodes = parseInt(document.getElementById("wizEpisodesCount").value) || 4;
    const words_per_episode = parseInt(document.getElementById("wizWordsPerEpisode").value) || 1200;
    const perspective = document.getElementById("wizPerspective").value;
    const ending = document.getElementById("wizEnding").value;
    const auto_continue = document.getElementById("wizAutoContinue").checked;

    const payload = {
        title: title || undefined,
        premise: premise || undefined,
        genre: genre,
        prose_style: prose_style,
        theme: theme,
        tone: tone,
        country: "United Kingdom",
        city: city || "London",
        era: era || "Contemporary",
        world_rules: rules,
        locations: locations,
        characters: characters,
        total_episodes: total_episodes,
        words_per_episode: words_per_episode,
        perspective: perspective,
        ending: ending,
        auto_continue: auto_continue,
        start_now: true
    };

    try {
        const res = await fetchWithAuth("/api/novels", {
            method: "POST",
            body: JSON.stringify(payload)
        });
        const novel = await res.json();
        showToast("Novel initiated! Directing story matrix...", "success");
        openNovel(novel.novel_id);
    } catch (e) {
        showToast("Error creating novel: " + e.message, "error");
    }
}

// Open Novel View
async function openNovel(novelId) {
    currentNovelId = novelId;
    navigateTo("novel");
    await refreshNovelView();
    startProgressPolling();
}

async function refreshNovelView() {
    if (!currentNovelId) return;
    try {
        const res = await fetch(`/api/novels/${currentNovelId}`);
        currentNovel = await res.json();
        
        document.getElementById("novelTitle").innerText = currentNovel.title;
        document.getElementById("novelLogline").innerText = currentNovel.logline || currentNovel.premise || "World architect is assembling the narrative...";
        
        const badge = document.getElementById("novelStatusBadge");
        badge.innerText = currentNovel.status;
        badge.className = `badge ${currentNovel.status === 'Completed' ? 'badge-completed' : (currentNovel.status === 'Writing Episode' ? 'badge-writing' : 'badge-ready')}`;

        // Cast Tab with Authentic Portraits
        const castGrid = document.getElementById("castCardsGrid");
        castGrid.innerHTML = (currentNovel.cast.characters || []).map(c => {
            const avatarUrl = getCharacterAvatar(c.core.name, c.core.gender, c.core.occupation);
            return `
            <div class="character-dossier-card">
                <div class="character-dossier-header">
                    <div class="character-avatar">
                        <img src="${avatarUrl}" alt="${c.core.name}" loading="lazy">
                    </div>
                    <div>
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <strong style="font-size: 1.15rem; color: var(--text-primary);">${c.core.name}</strong>
                            <span class="badge ${c.is_main ? 'badge-ready' : 'badge-draft'}">${c.core.role}</span>
                        </div>
                        <div style="font-size: 0.85rem; color: var(--text-tertiary); font-weight: 500;">
                            ${c.core.occupation || 'Unspecified'} · ${c.core.temperament || ''}
                        </div>
                    </div>
                </div>

                <div class="character-dossier-traits">
                    <div class="trait-row">
                        <span class="trait-label" style="display: flex; align-items: center; gap: 4px;">${ICONS.target} Want</span>
                        <span style="color: var(--text-primary); font-size: 0.88rem;">${c.motivation.want || 'Formulating'}</span>
                    </div>
                    <div class="trait-row">
                        <span class="trait-label" style="display: flex; align-items: center; gap: 4px;">${ICONS.seedling} Need</span>
                        <span style="color: var(--text-primary); font-size: 0.88rem;">${c.motivation.need || 'Formulating'}</span>
                    </div>
                    <div class="trait-row">
                        <span class="trait-label" style="color: var(--danger); display: flex; align-items: center; gap: 4px;">${ICONS.lock} Secret</span>
                        <span style="color: var(--text-primary); font-size: 0.88rem;">${c.motivation.secret || 'Guarded'}</span>
                    </div>
                </div>
            </div>
            `;
        }).join("");

        // World Tab
        const worldDiv = document.getElementById("worldDetailsContent");
        worldDiv.innerHTML = `
            <div style="margin-bottom: 24px;">
                <h4 style="font-weight: 800; font-size: 1.05rem; margin-bottom: 8px;">Geography & Era</h4>
                <p style="color: var(--text-secondary);">${currentNovel.world.city}, ${currentNovel.world.country} · Era: ${currentNovel.world.era} · Timeline: ${currentNovel.world.story_time_span}</p>
            </div>
            <div style="margin-bottom: 24px;">
                <h4 style="font-weight: 800; font-size: 1.05rem; margin-bottom: 8px;">Immutable World Rules</h4>
                <ul style="padding-left: 20px; line-height: 2; color: var(--text-secondary);">
                    ${(currentNovel.world.world_rules || []).map(r => `<li>${r}</li>`).join("") || '<li>No explicit rules recorded.</li>'}
                </ul>
            </div>
            <div>
                <h4 style="font-weight: 800; font-size: 1.05rem; margin-bottom: 14px;">Key Atmospheric Locations</h4>
                <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 14px;">
                    ${(currentNovel.world.locations || []).map(l => `
                        <div class="card" style="padding: 16px; margin: 0; background: var(--bg-surface-subtle);">
                            <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 6px;">
                                <span style="color: var(--accent);">${ICONS.mapPin}</span>
                                <strong style="color: var(--text-primary); font-size: 0.95rem;">${l.name}</strong>
                            </div>
                            <div style="font-size: 0.85rem; color: var(--text-secondary);">${l.description || l.atmosphere || ''}</div>
                        </div>
                    `).join("")}
                </div>
            </div>
        `;

        // Synopsis Tab
        const synDiv = document.getElementById("synopsisContent");
        synDiv.innerHTML = `
            <div style="line-height: 2; margin-bottom: 24px;">
                <h4 style="font-weight: 800; font-size: 1.05rem; margin-bottom: 8px;">Full Narrative Synopsis</h4>
                <p style="color: var(--text-secondary);">${currentNovel.synopsis || 'Structuring narrative overview...'}</p>
            </div>
            <div>
                <h4 style="font-weight: 800; font-size: 1.05rem; margin-bottom: 8px;">Opening Hook</h4>
                <blockquote style="border-left: 3px solid var(--accent); padding-left: 16px; font-style: italic; color: var(--text-primary); font-size: 1.05rem;">
                    "${currentNovel.hook || '...'}"
                </blockquote>
            </div>
        `;

        await loadEpisodesList();

    } catch (e) {
        console.error("Refresh error:", e);
    }
}

async function loadEpisodesList() {
    const listDiv = document.getElementById("episodesList");
    try {
        const res = await fetch(`/api/novels/${currentNovelId}/episodes`);
        const episodes = await res.json();
        
        if (episodes.length === 0) {
            listDiv.innerHTML = `
                <div style="text-align: center; padding: 50px 20px; color: var(--text-secondary);">
                    <div style="width: 52px; height: 52px; margin: 0 auto 16px; border-radius: 50%; background: var(--accent-subtle); display: flex; align-items: center; justify-content: center; color: var(--accent);">
                        ${ICONS.quill}
                    </div>
                    <div style="font-weight: 800; font-size: 1.15rem; margin-bottom: 6px;">No chapters written yet for this novel.</div>
                    <p style="font-size: 0.92rem; color: var(--text-tertiary); margin-bottom: 18px;">World and story matrix are ready. You can commence with Chapter 1.</p>
                    <button class="btn btn-primary" onclick="triggerWriteNext()">
                        ${ICONS.quill}
                        Write Chapter 1
                    </button>
                </div>
            `;
            return;
        }

        listDiv.innerHTML = episodes.map(ep => `
            <div class="chapter-list-item" onclick="openReader(${ep.episode_number})">
                <div style="display: flex; align-items: center; gap: 16px; flex: 1; min-width: 0;">
                    <div class="chapter-thumb-container">
                        <img src="/api/novels/${currentNovelId}/episodes/${ep.episode_number}/image" 
                             alt="Chapter ${ep.episode_number} Art" 
                             class="chapter-thumb-img" 
                             loading="lazy"
                             onerror="this.parentElement.style.display='none'">
                    </div>
                    <div style="min-width: 0; flex: 1;">
                        <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px; flex-wrap: wrap;">
                            <span class="badge badge-ready">Chapter ${ep.episode_number}</span>
                            <strong style="font-size: 1.15rem; color: var(--text-primary); text-overflow: ellipsis; overflow: hidden; white-space: nowrap;">${ep.title}</strong>
                        </div>
                        <div style="font-size: 0.9rem; color: var(--text-secondary); line-height: 1.5; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;">${ep.summary || ''}</div>
                    </div>
                </div>
                <div style="display: flex; align-items: center; gap: 14px; flex-shrink: 0;">
                    <span style="font-size: 0.85rem; color: var(--text-tertiary); font-weight: 600; display: flex; align-items: center; gap: 6px;">
                        ${ICONS.clock} ${Math.ceil(ep.word_count / 220)} min read
                    </span>
                    <button class="btn btn-secondary btn-sm" onclick="event.stopPropagation(); openReader(${ep.episode_number})">
                        ${ICONS.book}
                        Read Chapter
                    </button>
                </div>
            </div>
        `).join("");

    } catch (e) {
        console.error("Episodes list error:", e);
    }
}

// Progress Polling with 6-stage highlights
function startProgressPolling() {
    stopProgressPolling();
    progressPollTimer = setInterval(async () => {
        if (!currentNovelId) return;
        try {
            const res = await fetch(`/api/novels/${currentNovelId}/progress`);
            const p = await res.json();
            const card = document.getElementById("novelProgressCard");
            
            if (p.is_active || (p.percentage > 0 && p.percentage < 100)) {
                card.style.display = "block";
                document.getElementById("progressStepTitle").innerText = p.current_step;
                document.getElementById("progressPercentage").innerText = p.percentage + "%";
                document.getElementById("progressFill").style.width = p.percentage + "%";
                document.getElementById("progressDetail").innerText = `Stage ${p.step_number} of ${p.total_steps} (Chapter ${p.current_episode} of ${p.total_episodes})`;

                for (let i = 1; i <= 6; i++) {
                    const el = document.getElementById(`stage${i}Ind`);
                    if (el) {
                        if (i === p.step_number) el.className = "stage-step active";
                        else if (i < p.step_number) el.className = "stage-step completed";
                        else el.className = "stage-step";
                    }
                }
            } else {
                card.style.display = "none";
                if (p.last_error) {
                    showToast("Generation Error: " + p.last_error, "error");
                }
                await refreshNovelView();
            }
        } catch (e) {}
    }, 1500);
}

function stopProgressPolling() {
    if (progressPollTimer) {
        clearInterval(progressPollTimer);
        progressPollTimer = null;
    }
}

// Write Next Episode
async function triggerWriteNext() {
    try {
        const res = await fetch(`/api/novels/${currentNovelId}/write-next`, { method: "POST" });
        if (!res.ok) {
            const err = await res.json();
            showToast(err.detail || "Error initiating generation", "error");
            return;
        }
        showToast("Generating next chapter...", "info");
        startProgressPolling();
    } catch (e) {
        showToast("Error: " + e.message, "error");
    }
}

// Delete Novel
async function confirmDeleteNovel() {
    if (!confirm("Are you sure you want to permanently delete this novel and all chapters?")) return;
    try {
        await fetch(`/api/novels/${currentNovelId}`, { method: "DELETE" });
        showToast("Novel removed from Author's Desk", "info");
        navigateTo('library');
    } catch (e) {
        showToast("Error deleting novel: " + e.message, "error");
    }
}

// Tabs Switcher
function switchNovelTab(tabName) {
    const tabs = ["episodes", "cast", "world", "synopsis"];
    tabs.forEach(t => {
        document.getElementById(`tab${t.charAt(0).toUpperCase() + t.slice(1)}`).style.display = (t === tabName) ? "block" : "none";
    });
    document.querySelectorAll(".tab-nav .tab-btn").forEach((btn, idx) => {
        btn.className = (tabs[idx] === tabName) ? "tab-btn active" : "tab-btn";
    });
}

// Reader
async function openReader(episodeNumber) {
    currentEpisodeNumber = episodeNumber;
    navigateTo("reader");
    
    try {
        const res = await fetch(`/api/novels/${currentNovelId}/episodes/${episodeNumber}`);
        currentEpisodeData = await res.json();

        // Update Chapter Artwork Hero
        const heroContainer = document.getElementById("readerHeroContainer");
        const heroImg = document.getElementById("readerHeroImg");
        const heroLoc = document.getElementById("readerHeroLocation");
        
        if (heroContainer && heroImg) {
            heroImg.src = `/api/novels/${currentNovelId}/episodes/${episodeNumber}/image`;
            heroContainer.style.display = "block";
            
            const firstScene = (currentEpisodeData.scenes && currentEpisodeData.scenes[0]) ? currentEpisodeData.scenes[0] : null;
            if (firstScene && firstScene.location_key) {
                heroLoc.innerText = `${firstScene.location_key} · ${firstScene.time_marker || 'Scene'}`;
            } else if (currentNovel && currentNovel.world) {
                heroLoc.innerText = `${currentNovel.world.city} · ${currentNovel.world.era}`;
            } else {
                heroLoc.innerText = currentEpisodeData.title;
            }
        }

        document.getElementById("readerEpisodeNum").innerText = `Chapter ${currentEpisodeData.episode_number}`;
        document.getElementById("readerEpisodeTitle").innerText = currentEpisodeData.title;
        document.getElementById("readerPovChar").innerText = currentEpisodeData.pov_character;
        document.getElementById("readerWordCount").innerText = `${currentEpisodeData.word_count.toLocaleString()} words`;
        document.getElementById("readerReadTime").innerText = `~${Math.ceil(currentEpisodeData.word_count / 220)} min read`;

        const paragraphs = currentEpisodeData.content.split("\n\n").filter(p => p.trim());
        document.getElementById("readerContent").innerHTML = paragraphs.map(p => `<p>${p}</p>`).join("");

        renderBehindTheScenes(currentEpisodeData.scenes);

    } catch (e) {
        showToast("Error loading chapter: " + e.message, "error");
    }
}

// Regenerate Chapter Artwork
async function regenerateCurrentChapterArt() {
    if (!currentNovelId || !currentEpisodeNumber) return;
    const btn = document.getElementById("btnRegenerateArt");
    if (!btn) return;
    
    const origHtml = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = `
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="animation: spin 1s linear infinite;">
            <line x1="12" y1="2" x2="12" y2="6"></line>
            <line x1="12" y1="18" x2="12" y2="22"></line>
            <line x1="4.93" y1="4.93" x2="7.76" y2="7.76"></line>
            <line x1="16.24" y1="16.24" x2="19.07" y2="19.07"></line>
            <line x1="2" y1="12" x2="6" y2="12"></line>
            <line x1="18" y1="12" x2="22" y2="12"></line>
            <line x1="4.93" y1="19.07" x2="7.76" y2="16.24"></line>
            <line x1="16.24" y1="7.76" x2="19.07" y2="4.93"></line>
        </svg>
        <span>Creating...</span>
    `;

    try {
        showToast("Synthesizing tailored scene illustration...", "info");
        const res = await fetch(`/api/novels/${currentNovelId}/episodes/${currentEpisodeNumber}/generate-image`, {
            method: "POST"
        });
        const data = await res.json();
        if (data.success) {
            const heroImg = document.getElementById("readerHeroImg");
            if (heroImg) {
                heroImg.src = `${data.image_url}?t=${Date.now()}`;
            }
            showToast("Chapter artwork updated successfully!", "success");
        } else {
            showToast("Failed to regenerate artwork", "error");
        }
    } catch (e) {
        showToast("Error generating artwork: " + e.message, "error");
    } finally {
        btn.disabled = false;
        btn.innerHTML = origHtml;
    }
}


function toggleFontSize(delta) {
    readerFontSize = Math.max(1.0, Math.min(2.0, readerFontSize + delta * 0.1));
    document.getElementById("readerContent").style.fontSize = `${readerFontSize}rem`;
}

function toggleDrawer() {
    const drawer = document.getElementById("behindTheScenesDrawer");
    drawer.classList.toggle("open");
}

function renderBehindTheScenes(scenes) {
    const container = document.getElementById("drawerContent");
    if (!scenes || scenes.length === 0) {
        container.innerHTML = `<p style="color: var(--text-tertiary); text-align: center; padding: 40px;">No scene simulation records available.</p>`;
        return;
    }

    container.innerHTML = scenes.map(s => `
        <div class="scene-block">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span style="color: var(--accent);">${ICONS.theater}</span>
                    <strong style="color: var(--text-primary); font-size: 1.05rem;">Scene ${s.scene_number}: ${s.title}</strong>
                </div>
                <span class="badge badge-draft" style="font-size: 0.74rem;">${s.time_marker} · ${s.location_key}</span>
            </div>
            
            <div style="font-size: 0.86rem; color: var(--text-secondary); line-height: 1.6; margin-bottom: 14px;">
                <div style="display: flex; align-items: flex-start; gap: 6px; margin-bottom: 4px;">
                    <span style="color: var(--accent);">${ICONS.target}</span>
                    <span><strong>Goal:</strong> ${s.goal}</span>
                </div>
                <div style="display: flex; align-items: flex-start; gap: 6px;">
                    <span style="color: var(--gold);">${ICONS.alert}</span>
                    <span><strong>Conflict:</strong> ${s.conflict}</span>
                </div>
            </div>

            <div style="font-size: 0.8rem; font-weight: 800; color: var(--text-tertiary); text-transform: uppercase; letter-spacing: 0.05em; margin-bottom: 10px;">Multi-Agent Actor Turns</div>
            
            ${(s.turns || []).map(t => {
                const charObj = (currentNovel?.cast?.characters || []).find(c => c.core.name === t.character_key);
                const avatar = getCharacterAvatar(t.character_key, charObj?.core?.gender, charObj?.core?.occupation);
                return `
                <div class="turn-card">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <img src="${avatar}" style="width: 24px; height: 24px; border-radius: 50%; object-fit: cover;" alt="${t.character_key}">
                            <strong style="color: var(--accent); font-size: 0.95rem;">${t.character_key}</strong>
                        </div>
                        <span style="font-size: 0.76rem; color: var(--text-tertiary); font-weight: 600;">Emotion: ${t.emotion}</span>
                    </div>

                    <div style="font-size: 0.88rem; margin: 6px 0; color: var(--text-secondary);">
                        <strong style="color: var(--text-primary);">Action:</strong> ${t.action}
                    </div>

                    ${t.dialogue ? `
                        <div style="font-size: 0.92rem; color: var(--text-primary); background: var(--bg-surface-subtle); padding: 8px 12px; border-radius: 6px; margin: 8px 0; border-left: 3px solid var(--accent);">
                            "${t.dialogue}"
                        </div>
                    ` : ''}
                    
                    <div class="thought-box">
                        <div style="display: flex; align-items: center; gap: 6px; font-weight: 700; color: var(--danger); font-size: 0.78rem; text-transform: uppercase;">
                            ${ICONS.lock} Secret Internal Thought
                        </div>
                        <div style="margin-top: 4px;">"${t.thought}"</div>
                    </div>

                    ${t.knowledge_gain ? `
                        <div style="font-size: 0.8rem; color: var(--success); margin-top: 8px; font-weight: 600; display: flex; align-items: center; gap: 6px;">
                            ${ICONS.lightbulb}
                            <span>Knowledge Acquired: ${t.knowledge_gain}</span>
                        </div>
                    ` : ''}
                </div>
                `;
            }).join("")}
        </div>
    `).join("");
}

// ==================== AUTHENTICATION & USER MANAGEMENT ====================

async function checkAuthStatus() {
    if (!authToken) {
        currentUser = null;
        updateUserNavUI();
        return;
    }
    try {
        const res = await fetchWithAuth("/api/auth/me");
        if (res.ok) {
            currentUser = await res.json();
        } else {
            currentUser = null;
            authToken = null;
            localStorage.removeItem("st_auth_token");
        }
    } catch (e) {
        console.error("Auth check failed:", e);
    }
    updateUserNavUI();
}

function updateUserNavUI() {
    const guestSection = document.getElementById("navGuestSection");
    const userSection = document.getElementById("navUserSection");
    const navLinkAdmin = document.getElementById("navLinkAdmin");
    const dropdownAdminLink = document.getElementById("dropdownAdminLink");
    const navUserName = document.getElementById("navUserName");
    const navUserAvatar = document.getElementById("navUserAvatar");
    const navUserRoleBadge = document.getElementById("navUserRoleBadge");

    if (currentUser) {
        if (guestSection) guestSection.style.display = "none";
        if (userSection) userSection.style.display = "block";
        const displayName = currentUser.full_name || currentUser.username;
        if (navUserName) navUserName.innerText = displayName;
        if (navUserAvatar) navUserAvatar.innerText = displayName.charAt(0).toUpperCase();

        const isAdmin = (currentUser.role === "admin");
        if (navUserRoleBadge) {
            navUserRoleBadge.innerText = isAdmin ? "Admin" : "Author";
            navUserRoleBadge.className = isAdmin ? "badge badge-role-admin" : "badge badge-role-author";
        }
        if (navLinkAdmin) navLinkAdmin.style.display = isAdmin ? "inline-flex" : "none";
        if (dropdownAdminLink) dropdownAdminLink.style.display = isAdmin ? "flex" : "none";
    } else {
        if (guestSection) guestSection.style.display = "flex";
        if (userSection) userSection.style.display = "none";
        if (navLinkAdmin) navLinkAdmin.style.display = "none";
        if (dropdownAdminLink) dropdownAdminLink.style.display = "none";
    }
}

function toggleUserDropdown(event) {
    if (event) event.stopPropagation();
    const menu = document.getElementById("userDropdownMenu");
    if (menu) {
        menu.classList.toggle("show");
    }
}

function openAuthModal(tab = "login") {
    const modal = document.getElementById("authModal");
    if (modal) {
        modal.style.display = "flex";
        switchAuthTab(tab);
    }
}

function closeAuthModal() {
    const modal = document.getElementById("authModal");
    if (modal) modal.style.display = "none";
}

function switchAuthTab(tab) {
    const loginForm = document.getElementById("authLoginForm");
    const regForm = document.getElementById("authRegisterForm");
    const tabBtnLogin = document.getElementById("authTabBtnLogin");
    const tabBtnReg = document.getElementById("authTabBtnRegister");
    const modalTitle = document.getElementById("authModalTitle");

    if (tab === "login") {
        if (loginForm) loginForm.style.display = "block";
        if (regForm) regForm.style.display = "none";
        if (tabBtnLogin) tabBtnLogin.className = "auth-tab-btn active";
        if (tabBtnReg) tabBtnReg.className = "auth-tab-btn";
        if (modalTitle) modalTitle.querySelector("span").innerText = "Sign In to Storyteller";
    } else {
        if (loginForm) loginForm.style.display = "none";
        if (regForm) regForm.style.display = "block";
        if (tabBtnLogin) tabBtnLogin.className = "auth-tab-btn";
        if (tabBtnReg) tabBtnReg.className = "auth-tab-btn active";
        if (modalTitle) modalTitle.querySelector("span").innerText = "Create Author Account";
    }
}

function fillDemoAdminLogin() {
    const idInput = document.getElementById("loginIdentifier");
    const pwdInput = document.getElementById("loginPassword");
    if (idInput) idInput.value = "admin@storyteller.ai";
    if (pwdInput) pwdInput.value = "admin123";
    switchAuthTab("login");
}

async function handleLoginSubmit(event) {
    event.preventDefault();
    const identifier = document.getElementById("loginIdentifier").value.trim();
    const password = document.getElementById("loginPassword").value;
    const btn = document.getElementById("btnLoginSubmit");
    const oldText = btn.innerHTML;
    btn.innerHTML = "Signing in...";
    btn.disabled = true;

    try {
        const res = await fetch("/api/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ identifier, password })
        });
        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.detail || "Authentication failed");
        }
        authToken = data.token;
        localStorage.setItem("st_auth_token", authToken);
        currentUser = data.user;
        updateUserNavUI();
        closeAuthModal();
        showToast(`Welcome back, ${currentUser.full_name || currentUser.username}!`, "success");
        await loadLibrary();
    } catch (e) {
        showToast(e.message, "error");
    } finally {
        btn.innerHTML = oldText;
        btn.disabled = false;
    }
}

async function handleRegisterSubmit(event) {
    event.preventDefault();
    const fullName = document.getElementById("regFullName").value.trim();
    const username = document.getElementById("regUsername").value.trim();
    const email = document.getElementById("regEmail").value.trim();
    const password = document.getElementById("regPassword").value;
    const btn = document.getElementById("btnRegisterSubmit");
    const oldText = btn.innerHTML;
    btn.innerHTML = "Creating account...";
    btn.disabled = true;

    try {
        const res = await fetch("/api/auth/register", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                username,
                email,
                password,
                full_name: fullName || undefined
            })
        });
        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.detail || "Registration failed");
        }
        authToken = data.token;
        localStorage.setItem("st_auth_token", authToken);
        currentUser = data.user;
        updateUserNavUI();
        closeAuthModal();
        showToast(`Account created! Welcome, ${currentUser.full_name || currentUser.username}!`, "success");
        await loadLibrary();
    } catch (e) {
        showToast(e.message, "error");
    } finally {
        btn.innerHTML = oldText;
        btn.disabled = false;
    }
}

async function handleLogout() {
    const dropdown = document.getElementById("userDropdownMenu");
    if (dropdown) dropdown.classList.remove("show");

    if (authToken) {
        try {
            await fetchWithAuth("/api/auth/logout", { method: "POST" });
        } catch (e) {
            console.error("Logout request error:", e);
        }
    }
    authToken = null;
    currentUser = null;
    localStorage.removeItem("st_auth_token");
    updateUserNavUI();
    showToast("Signed out successfully", "info");
    navigateTo("library");
}

// ==================== USER PROFILE MODAL ====================

async function openProfileModal() {
    const dropdown = document.getElementById("userDropdownMenu");
    if (dropdown) dropdown.classList.remove("show");

    if (!currentUser) {
        openAuthModal("login");
        return;
    }
    const modal = document.getElementById("profileModal");
    modal.style.display = "flex";

    // Refresh profile data
    try {
        const res = await fetchWithAuth("/api/auth/me");
        if (res.ok) {
            currentUser = await res.json();
        }
    } catch (e) {
        console.error("Profile refresh error:", e);
    }

    const displayName = currentUser.full_name || currentUser.username;
    document.getElementById("profileAvatarBig").innerText = displayName.charAt(0).toUpperCase();
    document.getElementById("profileDisplayName").innerText = displayName;
    document.getElementById("profileEmail").innerText = currentUser.email;
    const badge = document.getElementById("profileRoleBadge");
    if (badge) {
        badge.innerText = currentUser.role === "admin" ? "Platform Admin" : "Author";
        badge.className = currentUser.role === "admin" ? "badge badge-role-admin" : "badge badge-role-author";
    }
    document.getElementById("profileStoriesCount").innerText = currentUser.novels_count || 0;

    document.getElementById("profileEditFullName").value = currentUser.full_name || "";
    document.getElementById("profileEditBio").value = currentUser.bio || "";
    document.getElementById("profileCurrentPwd").value = "";
    document.getElementById("profileNewPwd").value = "";
}

function closeProfileModal() {
    const modal = document.getElementById("profileModal");
    if (modal) modal.style.display = "none";
}

async function handleProfileUpdateSubmit(event) {
    event.preventDefault();
    const fullName = document.getElementById("profileEditFullName").value.trim();
    const bio = document.getElementById("profileEditBio").value.trim();
    const currentPwd = document.getElementById("profileCurrentPwd").value;
    const newPwd = document.getElementById("profileNewPwd").value;
    const btn = document.getElementById("btnSaveProfile");
    const oldText = btn.innerHTML;
    btn.innerHTML = "Saving...";
    btn.disabled = true;

    try {
        const payload = {
            full_name: fullName,
            bio: bio
        };
        if (newPwd) {
            if (!currentPwd) {
                throw new Error("Current password is required to set a new password");
            }
            payload.current_password = currentPwd;
            payload.new_password = newPwd;
        }

        const res = await fetchWithAuth("/api/auth/profile", {
            method: "PATCH",
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok) {
            throw new Error(data.detail || "Failed to update profile");
        }
        currentUser = data;
        updateUserNavUI();
        closeProfileModal();
        showToast("Profile updated successfully", "success");
    } catch (e) {
        showToast(e.message, "error");
    } finally {
        btn.innerHTML = oldText;
        btn.disabled = false;
    }
}

// ==================== ADMIN CONSOLE ====================

async function loadAdminDashboard() {
    try {
        const dashRes = await fetchWithAuth("/api/admin/dashboard");
        if (dashRes.ok) {
            const stats = await dashRes.json();
            document.getElementById("kpiTotalUsers").innerText = (stats.total_users || 0).toLocaleString();
            document.getElementById("kpiTotalNovels").innerText = (stats.total_novels || 0).toLocaleString();
            document.getElementById("kpiTotalEpisodes").innerText = (stats.total_episodes || 0).toLocaleString();
            document.getElementById("kpiTotalWords").innerText = (stats.total_words || 0).toLocaleString();
        }

        const usersRes = await fetchWithAuth("/api/admin/users");
        if (usersRes.ok) {
            adminUsersCache = await usersRes.json();
            renderAdminUsersTable(adminUsersCache);
        }
    } catch (e) {
        showToast("Failed to load admin dashboard: " + e.message, "error");
    }
}

function switchAdminTab(tab) {
    const tabUsers = document.getElementById("tabBtnAdminUsers");
    const tabAI = document.getElementById("tabBtnAdminAI");
    const contentUsers = document.getElementById("adminTabUsersContent");
    const contentAI = document.getElementById("adminTabAIContent");

    if (tab === "users") {
        if (tabUsers) tabUsers.className = "tab-btn active";
        if (tabAI) tabAI.className = "tab-btn";
        if (contentUsers) contentUsers.style.display = "block";
        if (contentAI) contentAI.style.display = "none";
    } else {
        if (tabUsers) tabUsers.className = "tab-btn";
        if (tabAI) tabAI.className = "tab-btn active";
        if (contentUsers) contentUsers.style.display = "none";
        if (contentAI) contentAI.style.display = "block";
        loadAdminAiConfig();
    }
}

function renderAdminUsersTable(users) {
    const tbody = document.getElementById("adminUsersTableBody");
    if (!tbody) return;

    if (!users || users.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-tertiary); padding: 36px;">No users found matching query.</td></tr>`;
        return;
    }

    tbody.innerHTML = users.map(u => {
        const initials = (u.full_name || u.username).charAt(0).toUpperCase();
        const roleClass = u.role === "admin" ? "badge badge-role-admin" : "badge badge-role-author";
        const roleLabel = u.role === "admin" ? "Admin" : "Author";
        const statusClass = u.status === "active" ? "badge badge-user-active" : "badge badge-user-suspended";
        const statusLabel = u.status === "active" ? "Active" : "Suspended";
        const dateStr = u.created_at ? new Date(u.created_at).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' }) : "Recently";
        const isSelf = currentUser && currentUser.id === u.id;

        return `
            <tr>
                <td>
                    <div style="display: flex; align-items: center; gap: 12px;">
                        <div class="user-nav-avatar" style="width: 36px; height: 36px; font-size: 0.95rem;">${initials}</div>
                        <div>
                            <div style="font-weight: 700; color: var(--text-primary);">${u.full_name || u.username} ${isSelf ? '<span style="font-size: 0.72rem; color: var(--accent);">(You)</span>' : ''}</div>
                            <div style="font-size: 0.8rem; color: var(--text-tertiary);">${u.email} · @${u.username}</div>
                        </div>
                    </div>
                </td>
                <td><span class="${roleClass}">${roleLabel}</span></td>
                <td><span class="${statusClass}">${statusLabel}</span></td>
                <td>
                    <div style="display: flex; align-items: center; gap: 6px; font-weight: 700; color: var(--text-primary);">
                        ${ICONS.book}
                        <span>${u.novels_count}</span>
                    </div>
                </td>
                <td style="font-size: 0.85rem; color: var(--text-secondary);">${dateStr}</td>
                <td style="text-align: right;">
                    <div style="display: flex; justify-content: flex-end; gap: 6px;">
                        ${!isSelf ? `
                            <button class="table-action-btn" title="${u.status === 'active' ? 'Suspend Account' : 'Activate Account'}" onclick="toggleAdminUserStatus('${u.id}', '${u.status}')">
                                ${u.status === 'active' ? ICONS.lock : ICONS.check}
                            </button>
                            <button class="table-action-btn" title="Reset Password" onclick="openAdminResetPwdModal('${u.id}', '${u.username}')">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 20h9"/><path d="M16.5 3.5a2.121 2.121 0 0 1 3 3L7 19l-4 1 1-4L16.5 3.5z"/></svg>
                            </button>
                            <button class="table-action-btn danger" title="Delete User" onclick="deleteAdminUser('${u.id}', '${u.username}')">
                                ${ICONS.trash}
                            </button>
                        ` : `
                            <span style="font-size: 0.8rem; color: var(--text-tertiary); font-style: italic;">Current Session</span>
                        `}
                    </div>
                </td>
            </tr>
        `;
    }).join("");
}

function filterAdminUsersTable() {
    const query = document.getElementById("adminUserSearchInput").value.toLowerCase().trim();
    if (!query) {
        renderAdminUsersTable(adminUsersCache);
        return;
    }
    const filtered = adminUsersCache.filter(u => 
        (u.username && u.username.toLowerCase().includes(query)) ||
        (u.email && u.email.toLowerCase().includes(query)) ||
        (u.full_name && u.full_name.toLowerCase().includes(query))
    );
    renderAdminUsersTable(filtered);
}

async function toggleAdminUserStatus(userId, currentStatus) {
    const newStatus = (currentStatus === "active") ? "suspended" : "active";
    try {
        const res = await fetchWithAuth(`/api/admin/users/${userId}/status`, {
            method: "PATCH",
            body: JSON.stringify({ status: newStatus })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Status toggle failed");
        showToast(`User status set to ${newStatus}`, "success");
        await loadAdminDashboard();
    } catch (e) {
        showToast(e.message, "error");
    }
}

function openAdminResetPwdModal(userId, username) {
    document.getElementById("adminResetTargetUserId").value = userId;
    document.getElementById("adminResetTargetUser").innerText = `@${username}`;
    document.getElementById("adminResetNewPwdInput").value = "";
    document.getElementById("adminResetPwdModal").style.display = "flex";
}

function closeAdminResetPwdModal() {
    document.getElementById("adminResetPwdModal").style.display = "none";
}

async function handleAdminResetPasswordSubmit(event) {
    event.preventDefault();
    const userId = document.getElementById("adminResetTargetUserId").value;
    const newPassword = document.getElementById("adminResetNewPwdInput").value;
    try {
        const res = await fetchWithAuth(`/api/admin/users/${userId}/reset-password`, {
            method: "POST",
            body: JSON.stringify({ new_password: newPassword })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Password reset failed");
        closeAdminResetPwdModal();
        showToast("Author password reset successfully", "success");
    } catch (e) {
        showToast(e.message, "error");
    }
}

async function deleteAdminUser(userId, username) {
    if (!confirm(`Are you sure you want to delete user @${username}? This action cannot be undone.`)) {
        return;
    }
    try {
        const res = await fetchWithAuth(`/api/admin/users/${userId}`, {
            method: "DELETE"
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Failed to delete user");
        showToast(`User @${username} deleted`, "success");
        await loadAdminDashboard();
    } catch (e) {
        showToast(e.message, "error");
    }
}

async function loadAdminAiConfig() {
    try {
        const res = await fetchWithAuth("/api/admin/ai-config");
        if (!res.ok) return;
        const cfg = await res.json();

        // 1. Text LLM Config
        if (cfg.provider) document.getElementById("adminCfgProvider").value = cfg.provider;
        if (cfg.base_url) document.getElementById("adminCfgBaseUrl").value = cfg.base_url;
        if (cfg.model) document.getElementById("adminCfgModel").value = cfg.model;

        const maskedNotice = document.getElementById("adminApiKeyMaskedNotice");
        if (cfg.api_key_masked) {
            maskedNotice.innerText = `Current key: ${cfg.api_key_masked} (leave blank to retain)`;
        } else {
            maskedNotice.innerText = "No API key configured currently.";
        }

        // 2. Image Generation Config
        if (cfg.image_provider && document.getElementById("adminCfgImageProvider")) {
            document.getElementById("adminCfgImageProvider").value = cfg.image_provider;
        }
        if (cfg.image_base_url && document.getElementById("adminCfgImageBaseUrl")) {
            document.getElementById("adminCfgImageBaseUrl").value = cfg.image_base_url;
        }
        if (cfg.image_model && document.getElementById("adminCfgImageModel")) {
            document.getElementById("adminCfgImageModel").value = cfg.image_model;
        }

        const imgMaskedNotice = document.getElementById("adminImageApiKeyMaskedNotice");
        if (imgMaskedNotice) {
            if (cfg.image_api_key_masked) {
                imgMaskedNotice.innerText = `Current image key: ${cfg.image_api_key_masked} (leave blank to retain)`;
            } else {
                imgMaskedNotice.innerText = "Inherits global LLM API key if identical, or enter a dedicated key.";
            }
        }

        onAdminProviderChanged();
        onAdminImageProviderChanged();
    } catch (e) {
        console.error("Failed to load AI config:", e);
    }
}

function onAdminProviderChanged() {
    const prov = document.getElementById("adminCfgProvider").value;
    const isCustom = (prov === "custom");
    const isOllama = (prov === "ollama");
    const isMock = (prov === "mock");

    const presetsRow = document.getElementById("adminCustomPresetsRow");
    if (presetsRow) presetsRow.style.display = isCustom ? "block" : "none";

    const grpBaseUrl = document.getElementById("adminGrpBaseUrl");
    if (grpBaseUrl) grpBaseUrl.style.display = (isCustom || isOllama || prov === "openrouter") ? "block" : "none";

    const grpApiKey = document.getElementById("adminGrpApiKey");
    if (grpApiKey) grpApiKey.style.display = (isMock || isOllama) ? "none" : "block";

    const modelInput = document.getElementById("adminCfgModel");
    if (prov === "gemini") {
        modelInput.placeholder = "gemini-2.5-flash or gemini-1.5-pro";
        if (!modelInput.value || modelInput.value.includes("gpt")) modelInput.value = "gemini-2.5-flash";
    } else if (prov === "openai") {
        modelInput.placeholder = "gpt-4o-mini or gpt-4o";
        if (!modelInput.value || modelInput.value.includes("gemini")) modelInput.value = "gpt-4o-mini";
    } else if (prov === "custom") {
        modelInput.placeholder = "gpt-4o-mini, deepseek-chat, or custom model";
    }
}

function onAdminImageProviderChanged() {
    const prov = document.getElementById("adminCfgImageProvider")?.value || "auto";
    const isCustom = (prov === "custom");
    const isOpenAI = (prov === "openai");
    const isGemini = (prov === "gemini");
    const isExternal = (isCustom || isOpenAI || isGemini);

    const presetsRow = document.getElementById("adminImagePresetsRow");
    if (presetsRow) presetsRow.style.display = isCustom ? "block" : "none";

    const grpBaseUrl = document.getElementById("adminGrpImgBaseUrl");
    if (grpBaseUrl) grpBaseUrl.style.display = isCustom ? "block" : "none";

    const grpApiKey = document.getElementById("adminGrpImgApiKey");
    if (grpApiKey) grpApiKey.style.display = isExternal ? "block" : "none";

    const grpModel = document.getElementById("adminGrpImgModel");
    if (grpModel) grpModel.style.display = isExternal ? "block" : "none";

    const modelInput = document.getElementById("adminCfgImageModel");
    if (modelInput) {
        if (prov === "openai" && (!modelInput.value || modelInput.value.includes("flux") || modelInput.value.includes("imagen"))) {
            modelInput.value = "dall-e-3";
        } else if (prov === "gemini" && (!modelInput.value || modelInput.value.includes("dall"))) {
            modelInput.value = "imagen-3.0-generate-002";
        }
    }
}

function applyAdminCustomApiPreset(preset) {
    document.getElementById("adminCfgProvider").value = "custom";
    onAdminProviderChanged();

    const baseUrlInput = document.getElementById("adminCfgBaseUrl");
    const modelInput = document.getElementById("adminCfgModel");

    if (preset === "avalai") {
        baseUrlInput.value = "https://api.avalai.ir/v1";
        modelInput.value = "gpt-4o-mini";
    } else if (preset === "groq") {
        baseUrlInput.value = "https://api.groq.com/openai/v1";
        modelInput.value = "llama-3.3-70b-versatile";
    } else if (preset === "openrouter") {
        baseUrlInput.value = "https://openrouter.ai/api/v1";
        modelInput.value = "deepseek/deepseek-chat";
    } else if (preset === "lmstudio") {
        baseUrlInput.value = "http://localhost:1234/v1";
        modelInput.value = "local-model";
    }
    showToast(`Applied ${preset.toUpperCase()} narrative preset`, "info");
}

function applyAdminImagePreset(preset) {
    const provSelect = document.getElementById("adminCfgImageProvider");
    const baseUrlInput = document.getElementById("adminCfgImageBaseUrl");
    const modelInput = document.getElementById("adminCfgImageModel");

    if (preset === "avalai") {
        provSelect.value = "custom";
        baseUrlInput.value = "https://api.avalai.ir/v1";
        modelInput.value = "dall-e-3";
    } else if (preset === "openai") {
        provSelect.value = "openai";
        baseUrlInput.value = "https://api.openai.com/v1";
        modelInput.value = "dall-e-3";
    } else if (preset === "openrouter") {
        provSelect.value = "custom";
        baseUrlInput.value = "https://openrouter.ai/api/v1";
        modelInput.value = "black-forest-labs/flux-1-schnell";
    } else if (preset === "local") {
        provSelect.value = "custom";
        baseUrlInput.value = "http://localhost:7860/v1";
        modelInput.value = "sdxl";
    }
    onAdminImageProviderChanged();
    showToast(`Applied ${preset.toUpperCase()} image gateway preset`, "info");
}

async function testAdminAiConnection() {
    const provider = document.getElementById("adminCfgProvider").value;
    const apiKey = document.getElementById("adminCfgApiKey").value;
    const model = document.getElementById("adminCfgModel").value;
    const baseUrl = document.getElementById("adminCfgBaseUrl").value;
    const resultBox = document.getElementById("adminTestResultBox");
    const btn = document.getElementById("btnAdminTestConn");

    const oldText = btn.innerHTML;
    btn.innerHTML = `<span>Testing live narrative connection...</span>`;
    btn.disabled = true;
    resultBox.style.display = "none";

    try {
        const res = await fetchWithAuth("/api/admin/test-connection", {
            method: "POST",
            body: JSON.stringify({
                provider: provider,
                api_key: apiKey || undefined,
                model: model || undefined,
                base_url: baseUrl || undefined
            })
        });
        const data = await res.json();
        resultBox.style.display = "block";

        if (data.success) {
            resultBox.style.background = "var(--success-subtle)";
            resultBox.style.border = "1px solid var(--success)";
            resultBox.style.color = "var(--success)";
            resultBox.innerHTML = `
                <div style="font-weight: 700; display: flex; align-items: center; gap: 6px;">
                    ${ICONS.check} Story LLM Connected (${data.latency_ms} ms)
                </div>
                <div style="margin-top: 6px; font-size: 0.82rem; color: var(--text-primary);">Response: "${data.message}"</div>
            `;
        } else {
            resultBox.style.background = "var(--danger-subtle)";
            resultBox.style.border = "1px solid var(--danger)";
            resultBox.style.color = "var(--danger)";
            resultBox.innerHTML = `
                <div style="font-weight: 700; display: flex; align-items: center; gap: 6px;">
                    ${ICONS.alert} Story LLM Connection Failed
                </div>
                <div style="margin-top: 4px; font-size: 0.82rem;">${data.error || 'No response received.'}</div>
            `;
        }
    } catch (e) {
        resultBox.style.display = "block";
        resultBox.style.background = "var(--danger-subtle)";
        resultBox.style.border = "1px solid var(--danger)";
        resultBox.style.color = "var(--danger)";
        resultBox.innerHTML = `<div style="font-weight: 700; display: flex; align-items: center; gap: 6px;">${ICONS.alert} Network Error: ${e.message}</div>`;
    } finally {
        btn.innerHTML = oldText;
        btn.disabled = false;
    }
}

async function testAdminImageConnection() {
    const provider = document.getElementById("adminCfgImageProvider").value;
    const apiKey = document.getElementById("adminCfgImageApiKey").value;
    const model = document.getElementById("adminCfgImageModel").value;
    const baseUrl = document.getElementById("adminCfgImageBaseUrl").value;
    const resultBox = document.getElementById("adminImageTestResultBox");
    const btn = document.getElementById("btnAdminTestImageConn");

    const oldText = btn.innerHTML;
    btn.innerHTML = `<span>Testing live image API...</span>`;
    btn.disabled = true;
    resultBox.style.display = "none";

    try {
        const res = await fetchWithAuth("/api/admin/test-image-connection", {
            method: "POST",
            body: JSON.stringify({
                image_provider: provider,
                image_api_key: apiKey || undefined,
                image_model: model || undefined,
                image_base_url: baseUrl || undefined
            })
        });
        const data = await res.json();
        resultBox.style.display = "block";

        if (data.success) {
            resultBox.style.background = "var(--success-subtle)";
            resultBox.style.border = "1px solid var(--success)";
            resultBox.style.color = "var(--success)";
            resultBox.innerHTML = `
                <div style="font-weight: 700; display: flex; align-items: center; gap: 6px;">
                    ${ICONS.check} Image API Connected (${data.latency_ms} ms)
                </div>
                <div style="margin-top: 6px; font-size: 0.82rem; color: var(--text-primary);">${data.message}</div>
            `;
        } else {
            resultBox.style.background = "var(--danger-subtle)";
            resultBox.style.border = "1px solid var(--danger)";
            resultBox.style.color = "var(--danger)";
            resultBox.innerHTML = `
                <div style="font-weight: 700; display: flex; align-items: center; gap: 6px;">
                    ${ICONS.alert} Image API Test Failed
                </div>
                <div style="margin-top: 4px; font-size: 0.82rem;">${data.error || 'No image response received.'}</div>
            `;
        }
    } catch (e) {
        resultBox.style.display = "block";
        resultBox.style.background = "var(--danger-subtle)";
        resultBox.style.border = "1px solid var(--danger)";
        resultBox.style.color = "var(--danger)";
        resultBox.innerHTML = `<div style="font-weight: 700; display: flex; align-items: center; gap: 6px;">${ICONS.alert} Network Error: ${e.message}</div>`;
    } finally {
        btn.innerHTML = oldText;
        btn.disabled = false;
    }
}

async function saveAdminAiConfig() {
    // 1. Narrative LLM
    const provider = document.getElementById("adminCfgProvider").value;
    const apiKey = document.getElementById("adminCfgApiKey").value;
    const model = document.getElementById("adminCfgModel").value;
    const baseUrl = document.getElementById("adminCfgBaseUrl").value;

    // 2. Image Engine
    const imageProvider = document.getElementById("adminCfgImageProvider")?.value || "auto";
    const imageApiKey = document.getElementById("adminCfgImageApiKey")?.value || undefined;
    const imageBaseUrl = document.getElementById("adminCfgImageBaseUrl")?.value || undefined;
    const imageModel = document.getElementById("adminCfgImageModel")?.value || undefined;

    try {
        const res = await fetchWithAuth("/api/admin/ai-config", {
            method: "POST",
            body: JSON.stringify({
                provider: provider,
                api_key: apiKey || undefined,
                model: model || undefined,
                base_url: baseUrl || undefined,
                image_provider: imageProvider,
                image_api_key: imageApiKey,
                image_base_url: imageBaseUrl,
                image_model: imageModel
            })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || "Failed to save configuration");
        await checkSystemInfo();
        showToast("Global AI and Image configurations saved successfully!", "success");
        await loadAdminAiConfig();
    } catch (e) {
        showToast("Error saving configuration: " + e.message, "error");
    }
}
