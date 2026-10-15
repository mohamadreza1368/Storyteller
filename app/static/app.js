// Application State
let currentNovelId = null;
let currentNovel = null;
let currentEpisodeNumber = null;
let currentEpisodeData = null;
let readerFontSize = 1.25;
let progressPollTimer = null;

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
    await checkSystemInfo();
    await loadLibrary();
    if (document.querySelectorAll(".char-card").length === 0) {
        addCharacterCard("Julian Vance", "Main", "Male", "Archival Conservator", "Scarred Cynic");
        addCharacterCard("Clara Sterling", "Main", "Female", "Investigative Journalist", "Passionate Idealist");
    }
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
    document.getElementById("viewLibrary").style.display = (viewName === "library") ? "block" : "none";
    document.getElementById("viewWizard").style.display = (viewName === "wizard") ? "block" : "none";
    document.getElementById("viewNovel").style.display = (viewName === "novel") ? "block" : "none";
    document.getElementById("viewReader").style.display = (viewName === "reader") ? "block" : "none";

    if (viewName === "library") {
        stopProgressPolling();
        loadLibrary();
    }
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

// Load Library
async function loadLibrary() {
    const grid = document.getElementById("novelsGrid");
    grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: var(--text-tertiary); padding: 40px;">Preparing Author's Desk…</div>`;
    
    try {
        const res = await fetch("/api/novels");
        const novels = await res.json();
        
        if (novels.length === 0) {
            grid.innerHTML = `
                <div style="grid-column: 1/-1; text-align: center; padding: 70px 24px; background: var(--bg-surface); border-radius: var(--radius-lg); border: 2px dashed var(--border-subtle);">
                    <div style="font-size: 3.5rem; margin-bottom: 16px;">📚</div>
                    <h3 style="font-weight: 900; font-size: 1.5rem; margin-bottom: 8px;">Your Library is Empty</h3>
                    <p style="color: var(--text-secondary); max-width: 500px; margin: 0 auto 24px;">Start by launching one of our instant presets or crafting your own original premise.</p>
                    <button class="btn btn-primary" onclick="startNewNovel()" style="padding: 12px 28px; font-size: 1.05rem;">✨ Create First Novel</button>
                </div>
            `;
            return;
        }

        grid.innerHTML = novels.map(n => `
            <div class="novel-card" onclick="openNovel('${n.novel_id}')">
                <div>
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
                        <span class="badge ${n.status === 'Completed' ? 'badge-completed' : (n.status === 'Writing Episode' ? 'badge-writing' : 'badge-ready')}">
                            ${n.status === 'Writing Episode' ? '● ' : ''}${n.status}
                        </span>
                        <span style="font-size: 0.82rem; font-weight: 700; color: var(--text-tertiary);">${n.genre}</span>
                    </div>
                    <h3 style="font-size: 1.35rem; font-weight: 900; margin-bottom: 8px; color: var(--text-primary); line-height: 1.4;">${n.title}</h3>
                    <p style="color: var(--text-secondary); font-size: 0.92rem; line-height: 1.6; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; overflow: hidden;">
                        ${n.premise || 'No initial premise provided'}
                    </p>
                </div>
                <div style="margin-top: 24px; padding-top: 14px; border-top: 1px solid var(--border-subtle); display: flex; justify-content: space-between; font-size: 0.88rem; color: var(--text-tertiary); font-weight: 600;">
                    <span>📖 ${n.written_episodes} of ${n.total_episodes} Chapters</span>
                    <span>✍️ ${n.total_words ? n.total_words.toLocaleString() + ' words' : 'Draft'}</span>
                </div>
            </div>
        `).join("");

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
        alert(`Preset "${presetName}" loaded into the wizard!`);
    } catch (e) {
        alert("Error loading preset: " + e.message);
    }
}

// Magic AI Auto-Fill
async function triggerMagicAutoFill() {
    const prompt = document.getElementById("magicPromptInput").value.trim();
    if (!prompt) {
        alert("Please write a short sentence or premise in the input box.");
        return;
    }

    const btn = event.target;
    const oldText = btn.innerHTML;
    btn.innerHTML = "⏳ Generating...";
    btn.disabled = true;

    try {
        const res = await fetch("/api/novels/magic-blueprint", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ prompt: prompt })
        });
        const bp = await res.json();
        fillWizardWithBlueprint(bp);
        alert("✨ AI expanded your premise into complete characters, world rules, and plotlines!");
        setWizardStep(1);
    } catch (e) {
        alert("Error: " + e.message);
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
        const res = await fetch("/api/novels", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        });
        const novel = await res.json();
        openNovel(novel.novel_id);
    } catch (e) {
        alert("Error creating novel: " + e.message);
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

        // Cast Tab
        const castGrid = document.getElementById("castCardsGrid");
        castGrid.innerHTML = (currentNovel.cast.characters || []).map(c => `
            <div class="card" style="padding: 20px; margin: 0; background: var(--bg-surface-subtle); border: 1px solid var(--border-subtle);">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <strong style="font-size: 1.2rem; color: var(--accent);">${c.core.name}</strong>
                    <span class="badge ${c.is_main ? 'badge-ready' : 'badge-draft'}">${c.core.role} · ${c.core.gender}</span>
                </div>
                <div style="font-size: 0.88rem; color: var(--text-secondary); margin-bottom: 12px; font-weight: 600;">
                    ${c.core.occupation || 'Unspecified'} · ${c.core.temperament || ''}
                </div>
                <div style="font-size: 0.88rem; line-height: 1.7; border-top: 1px solid var(--border-subtle); padding-top: 10px;">
                    <div>🎯 <strong>Want:</strong> ${c.motivation.want || 'Formulating'}</div>
                    <div>🌱 <strong>Need:</strong> ${c.motivation.need || 'Formulating'}</div>
                    <div style="color: var(--danger);">🔒 <strong>Secret:</strong> ${c.motivation.secret || 'Guarded'}</div>
                </div>
            </div>
        `).join("");

        // World Tab
        const worldDiv = document.getElementById("worldDetailsContent");
        worldDiv.innerHTML = `
            <div style="margin-bottom: 24px;">
                <h4 style="font-weight: 800; font-size: 1.1rem; margin-bottom: 8px;">Geography & Era</h4>
                <p style="color: var(--text-secondary);">${currentNovel.world.city}, ${currentNovel.world.country} · Era: ${currentNovel.world.era} · Timeline: ${currentNovel.world.story_time_span}</p>
            </div>
            <div style="margin-bottom: 24px;">
                <h4 style="font-weight: 800; font-size: 1.1rem; margin-bottom: 8px;">Immutable World Rules</h4>
                <ul style="padding-left: 20px; line-height: 2; color: var(--text-secondary);">
                    ${(currentNovel.world.world_rules || []).map(r => `<li>${r}</li>`).join("") || '<li>No explicit rules recorded.</li>'}
                </ul>
            </div>
            <div>
                <h4 style="font-weight: 800; font-size: 1.1rem; margin-bottom: 12px;">Key Atmospheric Locations</h4>
                <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 14px;">
                    ${(currentNovel.world.locations || []).map(l => `
                        <div class="card" style="padding: 16px; margin: 0; background: var(--bg-surface-subtle);">
                            <strong style="color: var(--text-primary); font-size: 1rem;">📍 ${l.name}</strong>
                            <div style="font-size: 0.85rem; color: var(--text-secondary); margin-top: 6px;">${l.description || l.atmosphere || ''}</div>
                        </div>
                    `).join("")}
                </div>
            </div>
        `;

        // Synopsis Tab
        const synDiv = document.getElementById("synopsisContent");
        synDiv.innerHTML = `
            <div style="line-height: 2; margin-bottom: 24px;">
                <h4 style="font-weight: 800; font-size: 1.1rem; margin-bottom: 8px;">Full Narrative Synopsis</h4>
                <p style="color: var(--text-secondary);">${currentNovel.synopsis || 'Structuring narrative overview...'}</p>
            </div>
            <div>
                <h4 style="font-weight: 800; font-size: 1.1rem; margin-bottom: 8px;">Opening Hook</h4>
                <blockquote style="border-left: 4px solid var(--accent); padding-left: 16px; font-style: italic; color: var(--text-primary); font-size: 1.05rem;">
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
                    <div style="font-size: 2.5rem; margin-bottom: 10px;">✍️</div>
                    <div style="font-weight: 800; font-size: 1.15rem; margin-bottom: 6px;">No chapters written yet for this novel.</div>
                    <p style="font-size: 0.92rem; color: var(--text-tertiary); margin-bottom: 18px;">World and story matrix are ready. You can commence with Chapter 1.</p>
                    <button class="btn btn-primary" onclick="triggerWriteNext()">✍️ Write Chapter 1</button>
                </div>
            `;
            return;
        }

        listDiv.innerHTML = episodes.map(ep => `
            <div style="display: flex; justify-content: space-between; align-items: center; padding: 20px; background: var(--bg-surface-subtle); border-radius: var(--radius-md); border: 1px solid var(--border-subtle); cursor: pointer; transition: all 0.2s ease;" onclick="openReader(${ep.episode_number})" onmouseover="this.style.borderColor='var(--accent)'" onmouseout="this.style.borderColor='var(--border-subtle)'">
                <div>
                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 6px;">
                        <span class="badge badge-ready">Chapter ${ep.episode_number}</span>
                        <strong style="font-size: 1.2rem; color: var(--text-primary);">${ep.title}</strong>
                    </div>
                    <div style="font-size: 0.9rem; color: var(--text-secondary); line-height: 1.5;">${ep.summary || ''}</div>
                </div>
                <div style="display: flex; align-items: center; gap: 16px;">
                    <span style="font-size: 0.88rem; color: var(--text-tertiary); font-weight: 600;">⏱️ ${Math.ceil(ep.word_count / 220)} min read</span>
                    <button class="btn btn-secondary btn-sm">Read Chapter 📖</button>
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
                    alert("Generation Error: " + p.last_error);
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
            alert(err.detail || "Error initiating generation");
            return;
        }
        startProgressPolling();
    } catch (e) {
        alert("Error: " + e.message);
    }
}

// Delete Novel
async function confirmDeleteNovel() {
    if (!confirm("Are you sure you want to permanently delete this novel and all chapters?")) return;
    try {
        await fetch(`/api/novels/${currentNovelId}`, { method: "DELETE" });
        navigateTo('library');
    } catch (e) {
        alert("Error deleting novel: " + e.message);
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

        document.getElementById("readerEpisodeNum").innerText = `Chapter ${currentEpisodeData.episode_number}`;
        document.getElementById("readerEpisodeTitle").innerText = currentEpisodeData.title;
        document.getElementById("readerPovChar").innerText = currentEpisodeData.pov_character;
        document.getElementById("readerWordCount").innerText = `${currentEpisodeData.word_count.toLocaleString()} words`;
        document.getElementById("readerReadTime").innerText = `⏱️ ~${Math.ceil(currentEpisodeData.word_count / 220)} min read`;

        const paragraphs = currentEpisodeData.content.split("\n\n").filter(p => p.trim());
        document.getElementById("readerContent").innerHTML = paragraphs.map(p => `<p>${p}</p>`).join("");

        renderBehindTheScenes(currentEpisodeData.scenes);

    } catch (e) {
        alert("Error loading chapter: " + e.message);
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
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                <strong style="color: var(--accent); font-size: 1.15rem;">🎬 Scene ${s.scene_number}: ${s.title}</strong>
                <span class="badge badge-draft" style="font-size: 0.78rem;">${s.time_marker} · 📍 ${s.location_key}</span>
            </div>
            
            <div style="font-size: 0.88rem; color: var(--text-secondary); line-height: 1.6; margin-bottom: 14px;">
                <div>🎯 <strong>Dramatic Goal:</strong> ${s.goal}</div>
                <div>⚡ <strong>Immediate Conflict:</strong> ${s.conflict}</div>
            </div>

            <div style="font-size: 0.85rem; font-weight: 800; color: var(--text-primary); margin-bottom: 8px;">🎭 Multi-Agent Actor Turns:</div>
            
            ${(s.turns || []).map(t => `
                <div class="turn-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <strong style="color: var(--accent); font-size: 1rem;">👤 ${t.character_key}</strong>
                        <span style="font-size: 0.78rem; color: var(--text-tertiary); font-weight: 600;">Emotion: ${t.emotion}</span>
                    </div>
                    <div style="font-size: 0.92rem; margin: 8px 0; color: var(--text-primary);">
                        <strong>Physical Action:</strong> ${t.action}
                    </div>
                    ${t.dialogue ? `
                        <div style="font-size: 0.95rem; color: var(--text-primary); background: var(--bg-surface-subtle); padding: 8px 12px; border-radius: 6px; margin: 6px 0; border-left: 3px solid var(--accent);">
                            <strong>Spoken Dialogue:</strong> "${t.dialogue}"
                        </div>
                    ` : ''}
                    
                    <div class="thought-box">
                        <strong>🔒 Secret Internal Thought:</strong>
                        <div style="margin-top: 4px;">"${t.thought}"</div>
                    </div>

                    ${t.knowledge_gain ? `
                        <div style="font-size: 0.82rem; color: var(--success); margin-top: 8px; font-weight: 700;">
                            💡 New Knowledge Acquired: ${t.knowledge_gain}
                        </div>
                    ` : ''}
                </div>
            `).join("")}
        </div>
    `).join("");
}

// Settings Modal & Custom API Handling
async function openSettingsModal() {
    const modal = document.getElementById("settingsModal");
    const resultBox = document.getElementById("testResultBox");
    resultBox.style.display = "none";
    modal.style.display = "flex";

    try {
        const res = await fetch("/api/system/info");
        const info = await res.json();
        if (info.provider) {
            document.getElementById("cfgProvider").value = info.provider;
        }
        if (info.model) {
            document.getElementById("cfgModel").value = info.model;
        }
        if (info.base_url) {
            document.getElementById("cfgBaseUrl").value = info.base_url;
        }
        onProviderChanged();
    } catch (e) {
        console.error("Failed to load system info:", e);
    }
}

function closeSettingsModal() {
    document.getElementById("settingsModal").style.display = "none";
}

function onProviderChanged() {
    const prov = document.getElementById("cfgProvider").value;
    const isCustom = (prov === "custom");
    const isOllama = (prov === "ollama");
    const isMock = (prov === "mock");

    document.getElementById("customPresetsRow").style.display = isCustom ? "block" : "none";
    document.getElementById("grpBaseUrl").style.display = (isCustom || isOllama || prov === "openrouter") ? "block" : "none";
    document.getElementById("grpApiKey").style.display = (isMock || isOllama) ? "none" : "block";

    const modelInput = document.getElementById("cfgModel");
    if (prov === "gemini") {
        modelInput.placeholder = "gemini-2.5-flash or gemini-1.5-pro";
        if (!modelInput.value || modelInput.value.includes("gpt")) modelInput.value = "gemini-2.5-flash";
    } else if (prov === "openai") {
        modelInput.placeholder = "gpt-4o-mini or gpt-4o";
        if (!modelInput.value || modelInput.value.includes("gemini")) modelInput.value = "gpt-4o-mini";
    } else if (prov === "custom") {
        modelInput.placeholder = "gpt-4o-mini, deepseek-chat, or your custom server model";
    }
}

function applyCustomApiPreset(preset) {
    document.getElementById("cfgProvider").value = "custom";
    onProviderChanged();

    const baseUrlInput = document.getElementById("cfgBaseUrl");
    const modelInput = document.getElementById("cfgModel");

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
}

async function testConnection() {
    const provider = document.getElementById("cfgProvider").value;
    const apiKey = document.getElementById("cfgApiKey").value;
    const model = document.getElementById("cfgModel").value;
    const baseUrl = document.getElementById("cfgBaseUrl").value;
    const resultBox = document.getElementById("testResultBox");
    const btn = document.getElementById("btnTestConn");

    const oldText = btn.innerHTML;
    btn.innerHTML = `<span>⏳</span> Testing connection...`;
    btn.disabled = true;
    resultBox.style.display = "none";

    try {
        const res = await fetch("/api/system/test-connection", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
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
                <div><strong>✅ Connection Successful!</strong> (Latency: ${data.latency_ms} ms)</div>
                <div style="margin-top: 6px; font-size: 0.82rem; color: var(--text-primary);">Response: "${data.message}"</div>
            `;
        } else {
            resultBox.style.background = "var(--danger-subtle)";
            resultBox.style.border = "1px solid var(--danger)";
            resultBox.style.color = "var(--danger)";
            resultBox.innerHTML = `
                <div><strong>❌ Connection Failed:</strong></div>
                <div style="margin-top: 4px; font-size: 0.82rem;">${data.error || 'No response received.'}</div>
            `;
        }
    } catch (e) {
        resultBox.style.display = "block";
        resultBox.style.background = "var(--danger-subtle)";
        resultBox.style.border = "1px solid var(--danger)";
        resultBox.style.color = "var(--danger)";
        resultBox.innerHTML = `<div><strong>❌ Network Error:</strong> ${e.message}</div>`;
    } finally {
        btn.innerHTML = oldText;
        btn.disabled = false;
    }
}

async function saveSettings() {
    const provider = document.getElementById("cfgProvider").value;
    const apiKey = document.getElementById("cfgApiKey").value;
    const model = document.getElementById("cfgModel").value;
    const baseUrl = document.getElementById("cfgBaseUrl").value;

    try {
        const res = await fetch("/api/system/config", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                provider: provider,
                api_key: apiKey || undefined,
                model: model || undefined,
                base_url: baseUrl || undefined
            })
        });
        await res.json();
        closeSettingsModal();
        await checkSystemInfo();
        alert("✅ Configuration saved successfully!");
    } catch (e) {
        alert("Error saving configuration: " + e.message);
    }
}
