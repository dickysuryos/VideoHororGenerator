document.addEventListener("DOMContentLoaded", () => {
    // DOM Elements
    const form = document.getElementById("generator-form");
    const promptInput = document.getElementById("prompt");
    const referencesContainer = document.getElementById("references-container");
    const modelTypeSelect = document.getElementById("model-type");
    const aspectSelect = document.getElementById("aspect-ratio");
    const stepsInput = document.getElementById("steps");
    const stepsVal = document.getElementById("steps-val");
    const guidanceInput = document.getElementById("guidance");
    const guidanceVal = document.getElementById("guidance-val");
    const seedInput = document.getElementById("seed");
    const btnSubmit = document.getElementById("btn-submit");

    const portalIdle = document.getElementById("portal-idle");
    const portalLoading = document.getElementById("portal-loading");
    const portalVideoContainer = document.getElementById("portal-video-container");
    const outputPlayer = document.getElementById("output-player");
    const loadingPct = document.getElementById("loading-pct");
    const loadingBar = document.getElementById("loading-bar");
    const loadingStatus = document.getElementById("loading-status");
    const terminalBody = document.getElementById("terminal-body");
    const manifestationCaption = document.getElementById("manifestation-caption");

    const metaExpandedPrompt = document.getElementById("meta-expanded-prompt");
    const metaModel = document.getElementById("meta-model");
    const metaRatio = document.getElementById("meta-ratio");
    const metaSteps = document.getElementById("meta-steps");
    const metaSeed = document.getElementById("meta-seed");

    const galleryContainer = document.getElementById("gallery-container");

    // Dynamic state
    let selectedGhostType = "none";
    let activeEventSource = null;
    let captionTypewriterInterval = null;

    // 1. Update sliders display values
    stepsInput.addEventListener("input", (e) => {
        stepsVal.textContent = e.target.value;
    });

    guidanceInput.addEventListener("input", (e) => {
        guidanceVal.textContent = parseFloat(e.target.value).toFixed(1);
    });

    // 2. Fetch and render Ghost References
    async function loadGhostReferences() {
        try {
            const res = await fetch("/api/references");
            if (!res.ok) throw new Error("Gagal mengambil referensi hantu.");
            const data = await res.json();
            
            // Clear but keep the "None" card
            referencesContainer.replaceChildren();
            
            // Create "None" Card first
            const noneCard = document.createElement("div");
            noneCard.className = "ref-card active";
            noneCard.setAttribute("data-type", "none");
            
            const noneImgPlaceholder = document.createElement("div");
            noneImgPlaceholder.className = "ref-card-img-placeholder";
            noneImgPlaceholder.textContent = "🔮";
            
            const noneInfo = document.createElement("div");
            noneInfo.className = "ref-card-info";
            const noneTitle = document.createElement("h3");
            noneTitle.textContent = "Tanpa Referensi";
            const noneDesc = document.createElement("p");
            noneDesc.textContent = "Murni deskripsi prompt tanpa mengacu hantu folklore khusus.";
            
            noneInfo.appendChild(noneTitle);
            noneInfo.appendChild(noneDesc);
            noneCard.appendChild(noneImgPlaceholder);
            noneCard.appendChild(noneInfo);
            referencesContainer.appendChild(noneCard);
            
            // Add click listener
            noneCard.addEventListener("click", () => selectGhostCard(noneCard, "none"));

            // Create cards for each ghost reference
            for (const [key, ghost] of Object.entries(data)) {
                const card = document.createElement("div");
                card.className = "ref-card";
                card.setAttribute("data-type", key);
                
                const img = document.createElement("img");
                // Select first image as representative thumbnail
                img.src = `/reference-image/${ghost.images[0]}`;
                img.alt = ghost.name;
                
                const info = document.createElement("div");
                info.className = "ref-card-info";
                const title = document.createElement("h3");
                title.textContent = ghost.name;
                const desc = document.createElement("p");
                desc.textContent = ghost.description;
                
                info.appendChild(title);
                info.appendChild(desc);
                card.appendChild(img);
                card.appendChild(info);
                referencesContainer.appendChild(card);
                
                card.addEventListener("click", () => selectGhostCard(card, key));
            }
        } catch (err) {
            console.error("Reference load error:", err);
            appendTerminalLine("Gagal memuat katalog referensi gambar dari server.", true);
        }
    }

    function selectGhostCard(cardElement, ghostType) {
        document.querySelectorAll(".ref-card").forEach(el => el.classList.remove("active"));
        cardElement.classList.add("active");
        selectedGhostType = ghostType;
    }

    // 3. Spooky Typewriter effect for captions
    function runTypewriter(text, element) {
        if (captionTypewriterInterval) clearInterval(captionTypewriterInterval);
        element.textContent = "";
        let i = 0;
        captionTypewriterInterval = setInterval(() => {
            if (i < text.length) {
                element.textContent += text.charAt(i);
                i++;
            } else {
                clearInterval(captionTypewriterInterval);
            }
        }, 35); // 35ms per character for spooky build up
    }

    // Helper: add line to logs terminal
    function appendTerminalLine(text, isError = false) {
        const line = document.createElement("div");
        line.className = "terminal-line" + (isError ? " error" : "");
        line.textContent = `> ${text}`;
        terminalBody.appendChild(line);
        terminalBody.scrollTop = terminalBody.scrollHeight;
    }

    // 4. Fetch and render Gallery History
    async function loadGalleryHistory() {
        try {
            const res = await fetch("/api/projects");
            if (!res.ok) throw new Error("Gagal memuat arsip.");
            const data = await res.json();
            
            galleryContainer.replaceChildren();
            
            if (data.length === 0) {
                const empty = document.createElement("div");
                empty.className = "no-history";
                empty.textContent = "Belum ada ritual mistis yang diarsipkan. Mulailah ritual pertamamu sekarang!";
                galleryContainer.appendChild(empty);
                return;
            }
            
            data.forEach(proj => {
                const card = document.createElement("div");
                card.className = "gallery-card";
                
                const thumb = document.createElement("div");
                thumb.className = "gallery-thumbnail";
                
                if (proj.status === "completed" && proj.video_url) {
                    const video = document.createElement("video");
                    video.src = proj.video_url;
                    video.muted = true;
                    video.playsInline = true;
                    
                    // Mouse hover play preview
                    card.addEventListener("mouseenter", () => video.play().catch(() => {}));
                    card.addEventListener("mouseleave", () => {
                        video.pause();
                        video.currentTime = 0;
                    });
                    
                    const btnPlay = document.createElement("button");
                    btnPlay.className = "btn-play-gallery";
                    btnPlay.textContent = "▶";
                    btnPlay.addEventListener("click", (e) => {
                        e.stopPropagation();
                        loadVideoIntoPortal(proj);
                    });
                    
                    thumb.appendChild(video);
                    thumb.appendChild(btnPlay);
                } else {
                    const icon = document.createElement("span");
                    icon.style.fontSize = "2.5rem";
                    icon.textContent = proj.status === "failed" ? "❌" : "⏳";
                    thumb.appendChild(icon);
                }
                
                const badge = document.createElement("div");
                badge.className = "gallery-card-badge";
                badge.textContent = proj.ghost_type !== "none" ? proj.ghost_type : "Murni";
                thumb.appendChild(badge);
                
                const details = document.createElement("div");
                details.className = "gallery-details";
                
                const title = document.createElement("h3");
                title.textContent = proj.prompt_original;
                
                const desc = document.createElement("p");
                desc.textContent = proj.indonesian_caption || "Menunggu pembuatan...";
                
                const metaRow = document.createElement("div");
                metaRow.className = "gallery-meta-row";
                
                const timeSpan = document.createElement("span");
                timeSpan.textContent = proj.timestamp;
                
                const modelSpan = document.createElement("span");
                modelSpan.textContent = proj.model_type === "14b" ? "Wan 14B" : "Wan 1.3B";
                
                metaRow.appendChild(modelSpan);
                metaRow.appendChild(timeSpan);
                
                details.appendChild(title);
                details.appendChild(desc);
                details.appendChild(metaRow);
                
                card.appendChild(thumb);
                card.appendChild(details);
                
                // Clicking card loads it
                card.addEventListener("click", () => {
                    if (proj.status === "completed") {
                        loadVideoIntoPortal(proj);
                    }
                });
                
                galleryContainer.appendChild(card);
            });
        } catch (err) {
            console.error("Gallery load error:", err);
        }
    }

    // Load static project info directly to display portal
    function loadVideoIntoPortal(proj) {
        portalIdle.classList.add("hidden");
        portalLoading.classList.add("hidden");
        portalVideoContainer.classList.remove("hidden");
        
        outputPlayer.src = proj.video_url;
        outputPlayer.load();
        
        // Show metadata details
        metaExpandedPrompt.textContent = proj.prompt_expanded || "Tidak ada prompt perluasan.";
        metaModel.textContent = proj.model_type === "14b" ? "Wan 2.1 14B (H100)" : "Wan 2.1 1.3B (H100)";
        metaRatio.textContent = proj.aspect_ratio.toUpperCase();
        metaSteps.textContent = proj.steps || "30";
        metaSeed.textContent = proj.seed !== -1 ? proj.seed : "Acak";
        
        // Run typewriter for Indonesian caption
        runTypewriter(proj.indonesian_caption || "", manifestationCaption);
        
        // Scroll to portal
        document.querySelector(".output-panel").scrollIntoView({ behavior: "smooth" });
    }

    // 5. Submit Form to trigger Generator Backend
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        const promptText = promptInput.value.trim();
        if (!promptText) return;
        
        // Disable UI
        btnSubmit.disabled = true;
        promptInput.disabled = true;
        modelTypeSelect.disabled = true;
        aspectSelect.disabled = true;
        
        // Switch Portal UI to Loading
        portalIdle.classList.add("hidden");
        portalVideoContainer.classList.add("hidden");
        portalLoading.classList.remove("hidden");
        
        // Clear terminal & set starting states
        terminalBody.replaceChildren();
        loadingPct.textContent = "0%";
        loadingBar.style.width = "0%";
        loadingStatus.textContent = "Menginisialisasi ritual...";
        
        appendTerminalLine("Memulai ritual pemanggilan horor...");
        appendTerminalLine(`Kategori Hantu: ${selectedGhostType.toUpperCase()}`);
        appendTerminalLine(`Model: Wan 2.1 ${modelTypeSelect.value.toUpperCase()}`);
        appendTerminalLine(`Aspek Rasio: ${aspectSelect.value}`);
        
        // Close any existing SSE stream
        if (activeEventSource) {
            activeEventSource.close();
        }
        
        try {
            const res = await fetch("/api/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    prompt: promptText,
                    ghost_type: selectedGhostType,
                    model_type: modelTypeSelect.value,
                    aspect_ratio: aspectSelect.value,
                    steps: parseInt(stepsInput.value),
                    guidance: parseFloat(guidanceInput.value),
                    seed: parseInt(seedInput.value)
                })
            });
            
            if (!res.ok) {
                const errData = await res.json();
                throw new Error(errData.detail || "Server mengalami masalah memproses ritual.");
            }
            
            const proj = await res.json();
            
            if (proj.status === "failed") {
                throw new Error(proj.logs[proj.logs.length - 1] || "Gagal di tahap persiapan.");
            }
            
            appendTerminalLine(`ID Proyek: ${proj.id}`);
            
            // Connect Server-Sent Events for live logs
            connectSSEStream(proj.id);
            
        } catch (err) {
            console.error("Submission failed:", err);
            appendTerminalLine(err.message, true);
            loadingStatus.textContent = "Ritual Gagal!";
            loadingPct.textContent = "FAIL";
            loadingBar.style.backgroundColor = "var(--accent-red)";
            resetFormInputs();
        }
    });

    function connectSSEStream(projectId) {
        appendTerminalLine("Membuka saluran komunikasi real-time...");
        activeEventSource = new EventSource(`/api/projects/${projectId}/logs/stream`);
        
        activeEventSource.onmessage = (e) => {
            try {
                const data = JSON.parse(e.data);
                
                // Append new logs safely
                if (data.log) {
                    appendTerminalLine(data.log);
                }
                
                // Update progress values
                if (data.progress !== undefined) {
                    loadingPct.textContent = `${data.progress}%`;
                    loadingBar.style.width = `${data.progress}%`;
                }
                
                if (data.status === "processing") {
                    loadingStatus.textContent = "Sedang memanifestasikan...";
                } else if (data.status === "completed") {
                    activeEventSource.close();
                    appendTerminalLine("Manifestasi selesai! Membuka portal visual...");
                    
                    // Fetch updated project details and show player
                    fetchProjectDetailsAndLoad(projectId);
                } else if (data.status === "failed") {
                    activeEventSource.close();
                    appendTerminalLine("Koneksi terputus. Ritual mengalami gangguan gaib.", true);
                    loadingStatus.textContent = "Ritual Terganggu!";
                    resetFormInputs();
                }
            } catch (err) {
                console.error("SSE Parsing error:", err);
            }
        };
        
        activeEventSource.onerror = (err) => {
            console.error("SSE Error:", err);
            activeEventSource.close();
            appendTerminalLine("Koneksi saluran log terputus dari server. Mengecek status...", true);
            // Fallback: poll status once
            setTimeout(() => checkProjectFinalStatus(projectId), 3000);
        };
    }

    async function checkProjectFinalStatus(projectId) {
        try {
            const res = await fetch(`/api/projects/${projectId}`);
            if (!res.ok) throw new Error();
            const proj = await res.json();
            
            if (proj.status === "completed") {
                loadVideoIntoPortal(proj);
                loadGalleryHistory();
            } else if (proj.status === "failed") {
                loadingStatus.textContent = "Ritual Gagal!";
                appendTerminalLine("Konfirmasi: Ritual gagal dilaporkan oleh server.", true);
            }
        } catch (e) {
            console.error(e);
        }
        resetFormInputs();
    }

    async function fetchProjectDetailsAndLoad(projectId) {
        try {
            const res = await fetch(`/api/projects/${projectId}`);
            if (!res.ok) throw new Error("Gagal mengambil rincian akhir.");
            const proj = await res.json();
            
            loadVideoIntoPortal(proj);
            loadGalleryHistory();
        } catch (err) {
            console.error(err);
            appendTerminalLine("Gagal memuat video setelah manifestasi selesai.", true);
        }
        resetFormInputs();
    }

    function resetFormInputs() {
        btnSubmit.disabled = false;
        promptInput.disabled = false;
        modelTypeSelect.disabled = false;
        aspectSelect.disabled = false;
    }

    // Init Page actions
    loadGhostReferences();
    loadGalleryHistory();
});
