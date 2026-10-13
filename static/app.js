// ==========================================================================
// COMPETITOR ANALYSIS AI AGENT - DASHBOARD CLIENT JAVASCRIPT
// Handles Server-Sent Events (SSE), reactive UI updates & data rendering
// ==========================================================================

document.addEventListener("DOMContentLoaded", () => {
    // Current Authenticated User
    let currentUser = null;

    async function checkAuth() {
        try {
            const res = await fetch("/api/auth/me", { credentials: "include" });
            if (!res.ok) {
                throw new Error("Unauthenticated");
            }
            const data = await res.json();
            if (!data.authenticated || !data.user) {
                throw new Error("Invalid session");
            }
            currentUser = data.user;
            setupUserUI(currentUser);
        } catch (err) {
            localStorage.removeItem("ca_user");
            localStorage.removeItem("ca_token");
            window.location.replace("/login");
        }
    }

    function setupUserUI(user) {
        const userProfileBadge = document.getElementById("userProfileBadge");
        const userNameDisplay = document.getElementById("userNameDisplay");
        const userAvatarSmall = document.getElementById("userAvatarSmall");
        const logoutBtn = document.getElementById("logoutBtn");

        if (userProfileBadge && userNameDisplay && userAvatarSmall) {
            userProfileBadge.style.display = "flex";
            userNameDisplay.textContent = user.full_name || user.email.split("@")[0];
            
            const initials = (user.full_name || user.email)
                .trim()
                .split(/\s+/)
                .map(n => n[0])
                .join("")
                .toUpperCase()
                .slice(0, 2);
            userAvatarSmall.textContent = initials || "AI";
        }

        if (logoutBtn) {
            logoutBtn.addEventListener("click", async () => {
                try {
                    await fetch("/api/auth/logout", {
                        method: "POST",
                        credentials: "include"
                    });
                } catch (e) {}
                localStorage.removeItem("ca_user");
                localStorage.removeItem("ca_token");
                window.location.replace("/login");
            });
        }
    }

    // Immediately guard the page
    checkAuth();

    // State Store
    const state = {
        isAnalyzing: false,
        eventSource: null,
        fullAnalysisData: {
            company_profile: null,
            market_data: null,
            market_share: null,
            local_competitors: [],
            national_competitors: [],
            global_competitors: [],
            local_competitors_detailed: [],
            swot_analysis: null,
            comparison_table: null,
            surpass_recommendations: null
        }
    };

    // DOM Elements
    const elements = {
        form: document.getElementById("analysisForm"),
        targetUrlInput: document.getElementById("targetUrlInput"),
        forceUpdateToggle: document.getElementById("forceUpdateToggle"),
        analyzeBtn: document.getElementById("analyzeBtn"),
        analyzeSpinner: document.getElementById("analyzeSpinner"),
        btnText: document.querySelector("#analyzeBtn .btn-text"),
        btnIcon: document.querySelector("#analyzeBtn .btn-icon"),
        
        progressSection: document.getElementById("progressSection"),
        currentStepText: document.getElementById("currentStepText"),
        progressPercent: document.getElementById("progressPercent"),
        progressBarFill: document.getElementById("progressBarFill"),
        
        errorBanner: document.getElementById("errorBanner"),
        errorMessage: document.getElementById("errorMessage"),
        closeErrorBtn: document.getElementById("closeErrorBtn"),
        
        dashboardContent: document.getElementById("dashboardContent"),
        initialEmptyState: document.getElementById("initialEmptyState"),
        exportJsonBtn: document.getElementById("exportJsonBtn"),
        
        // Tabs
        tabButtons: document.querySelectorAll(".tab-btn"),
        tabPanes: document.querySelectorAll(".tab-pane"),
        
        // Terminal
        eventTerminalBody: document.getElementById("eventTerminalBody"),
        clearLogsBtn: document.getElementById("clearLogsBtn")
    };

    // ======================================================================
    // TAB NAVIGATION & SIDEBAR CONTROLLER
    // ======================================================================
    const appSidebar = document.getElementById("appSidebar");
    const sidebarToggleBtn = document.getElementById("sidebarToggleBtn");
    const sidebarBottomExpandBtn = document.getElementById("sidebarBottomExpandBtn");
    const sidebarBrandWrap = document.getElementById("sidebarBrandWrap");
    const sidebarHomeBtn = document.getElementById("sidebarHomeBtn");

    function toggleSidebar(forceState) {
        if (!appSidebar) return;
        const isExpanded = typeof forceState === "boolean" 
            ? forceState 
            : !appSidebar.classList.contains("expanded");
        appSidebar.classList.toggle("expanded", isExpanded);
        localStorage.setItem("ca_sidebar_expanded", isExpanded ? "true" : "false");
    }

    if (sidebarToggleBtn) {
        sidebarToggleBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            toggleSidebar();
        });
    }
    if (sidebarBottomExpandBtn) {
        sidebarBottomExpandBtn.addEventListener("click", (e) => {
            e.stopPropagation();
            toggleSidebar();
        });
    }
    if (sidebarBrandWrap) {
        sidebarBrandWrap.addEventListener("click", () => {
            if (!appSidebar.classList.contains("expanded")) {
                toggleSidebar(true);
            } else {
                goToScanHero();
            }
        });
    }

    // Restore saved sidebar state
    if (localStorage.getItem("ca_sidebar_expanded") === "true" && appSidebar) {
        appSidebar.classList.add("expanded");
    }

    function goToScanHero() {
        window.scrollTo({ top: 0, behavior: "smooth" });
        if (sidebarHomeBtn) {
            sidebarHomeBtn.classList.add("active");
        }
        elements.tabButtons.forEach(b => b.classList.remove("active"));
        if (elements.targetUrlInput) {
            elements.targetUrlInput.focus();
        }
    }

    if (sidebarHomeBtn) {
        sidebarHomeBtn.addEventListener("click", goToScanHero);
    }

    elements.tabButtons.forEach(btn => {
        btn.addEventListener("click", () => {
            const targetTab = btn.getAttribute("data-tab");
            if (!targetTab) return;
            
            // Sync active state on all buttons targeting this tab (sidebar + dashboard header)
            elements.tabButtons.forEach(b => {
                b.classList.toggle("active", b.getAttribute("data-tab") === targetTab);
            });
            if (sidebarHomeBtn) {
                sidebarHomeBtn.classList.remove("active");
            }
            
            // Ensure dashboard is revealed
            if (elements.dashboardContent) {
                elements.dashboardContent.style.display = "block";
            }
            if (elements.initialEmptyState) {
                elements.initialEmptyState.style.display = "none";
            }

            // Switch active pane
            elements.tabPanes.forEach(pane => pane.classList.remove("active"));
            const targetPane = document.getElementById(targetTab);
            if (targetPane) {
                targetPane.classList.add("active");
            }

            // Smoothly scroll down so user sees the section
            if (elements.dashboardContent) {
                elements.dashboardContent.scrollIntoView({ behavior: "smooth", block: "start" });
            }

            // If mobile view, collapse drawer after navigation
            if (window.innerWidth < 768 && appSidebar && appSidebar.classList.contains("expanded")) {
                appSidebar.classList.remove("expanded");
            }
        });
    });

    // Make Hero Feature Cards interactive -> jump to corresponding tab
    document.querySelectorAll(".hero-feature-card").forEach((card, index) => {
        const tabMap = ["tab-overview", "tab-market", "tab-competitors", "tab-swot"];
        card.style.cursor = "pointer";
        card.addEventListener("click", () => {
            const targetTab = tabMap[index] || "tab-overview";
            const targetBtn = document.querySelector(`.tab-btn[data-tab="${targetTab}"]`);
            if (targetBtn) {
                targetBtn.click();
            }
        });
    });

    // Suggestion chips
    document.querySelectorAll(".chip").forEach(chip => {
        chip.addEventListener("click", () => {
            const url = chip.getAttribute("data-url");
            if (url) {
                elements.targetUrlInput.value = url;
                elements.form.dispatchEvent(new Event("submit"));
            }
        });
    });

    // Close error banner
    elements.closeErrorBtn.addEventListener("click", () => {
        elements.errorBanner.style.display = "none";
    });

    // Clear logs
    elements.clearLogsBtn.addEventListener("click", () => {
        elements.eventTerminalBody.innerHTML = '<div class="log-line info">Logs cleared.</div>';
    });

    // Export JSON
    elements.exportJsonBtn.addEventListener("click", () => {
        const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(state.fullAnalysisData, null, 2));
        const downloadAnchor = document.createElement("a");
        downloadAnchor.setAttribute("href", dataStr);
        const domain = (state.fullAnalysisData.company_profile?.name || "analysis").replace(/[^a-z0-9]/gi, "_").toLowerCase();
        downloadAnchor.setAttribute("download", `competitor_analysis_${domain}.json`);
        document.body.appendChild(downloadAnchor);
        downloadAnchor.click();
        downloadAnchor.remove();
    });

    // ======================================================================
    // LOGGING HELPER
    // ======================================================================
    function appendLog(type, message) {
        const line = document.createElement("div");
        line.className = `log-line ${type}`;
        const time = new Date().toLocaleTimeString();
        line.textContent = `[${time}] ${message}`;
        elements.eventTerminalBody.appendChild(line);
        elements.eventTerminalBody.scrollTop = elements.eventTerminalBody.scrollHeight;
    }

    // ======================================================================
    // PROGRESS STEPPER CONTROLLER
    // ======================================================================
    function updateProgress(stepText, percent, activeStepId) {
        if (elements.currentStepText) elements.currentStepText.textContent = stepText;
        if (elements.progressPercent) elements.progressPercent.textContent = `${percent}%`;
        if (elements.progressBarFill) elements.progressBarFill.style.width = `${percent}%`;

        const steps = ["step-crawl", "step-profile", "step-market", "step-competitors", "step-eval", "step-swot", "step-strategy"];
        let found = false;
        
        steps.forEach(id => {
            const el = document.getElementById(id);
            if (!el) return;
            if (id === activeStepId) {
                el.classList.add("active");
                el.classList.remove("done");
                found = true;
            } else if (!found) {
                el.classList.add("done");
                el.classList.remove("active");
            } else {
                el.classList.remove("active", "done");
            }
        });
    }

    // ======================================================================
    // SSE STREAM HANDLER
    // ======================================================================
    elements.form.addEventListener("submit", (e) => {
        e.preventDefault();
        const url = elements.targetUrlInput.value.trim();
        if (!url) return;

        startAnalysis(url, elements.forceUpdateToggle.checked);
    });

    function startAnalysis(url, forceUpdate) {
        // Reset state
        if (state.eventSource) {
            state.eventSource.close();
        }

        state.isAnalyzing = true;
        if (elements.analyzeBtn) elements.analyzeBtn.disabled = true;
        if (elements.analyzeSpinner) elements.analyzeSpinner.style.display = "inline-block";
        if (elements.btnIcon) elements.btnIcon.style.display = "none";
        if (elements.btnText) elements.btnText.textContent = "Analyzing...";

        if (elements.errorBanner) elements.errorBanner.style.display = "none";
        if (elements.progressSection) {
            elements.progressSection.style.display = "block";
            elements.progressSection.scrollIntoView({ behavior: "smooth", block: "nearest" });
        }
        if (elements.initialEmptyState) elements.initialEmptyState.style.display = "none";
        if (elements.dashboardContent) elements.dashboardContent.style.display = "block";
        if (elements.exportJsonBtn) elements.exportJsonBtn.style.display = "inline-flex";

        updateProgress("Initiating crawler session...", 10, "step-crawl");
        appendLog("status", `Connecting to extraction stream for: ${url}`);

        // Construct SSE URL with authenticated user ID and token
        const activeUserId = currentUser?.id || "test";
        let sseUrl = `/api/extract?url=${encodeURIComponent(url)}&user_id=${encodeURIComponent(activeUserId)}`;
        const localToken = localStorage.getItem("ca_token");
        if (localToken) {
            sseUrl += `&auth_token=${encodeURIComponent(localToken)}`;
        }
        if (forceUpdate) {
            sseUrl += "&update=true";
        }

        const eventSource = new EventSource(sseUrl);
        state.eventSource = eventSource;

        // Listen for all backend SSE events
        eventSource.addEventListener("status", (e) => {
            try {
                const data = JSON.parse(e.data);
                const step = data.step || "Processing...";
                appendLog("status", `Status: ${step}`);

                // Map status to progress bar
                const lower = step.toLowerCase();
                if (lower.includes("scraping") || lower.includes("crawler")) {
                    updateProgress(step, 20, "step-crawl");
                } else if (lower.includes("company profile") || lower.includes("profile")) {
                    updateProgress(step, 35, "step-profile");
                } else if (lower.includes("market")) {
                    updateProgress(step, 50, "step-market");
                } else if (lower.includes("competitor list")) {
                    updateProgress(step, 65, "step-competitors");
                } else if (lower.includes("analyzing:") || lower.includes("local competitors")) {
                    updateProgress(step, 75, "step-eval");
                } else if (lower.includes("swot")) {
                    updateProgress(step, 85, "step-swot");
                } else if (lower.includes("comparison table")) {
                    updateProgress(step, 90, "step-swot");
                } else if (lower.includes("recommendations")) {
                    updateProgress(step, 95, "step-strategy");
                } else {
                    elements.currentStepText.textContent = step;
                }
            } catch (err) {
                console.error("Error parsing status event:", err);
            }
        });

        eventSource.addEventListener("company_profile", (e) => {
            try {
                const data = JSON.parse(e.data);
                state.fullAnalysisData.company_profile = data;
                appendLog("event", `Received Company Profile: ${data.name || data.company_name || "Success"}`);
                renderCompanyProfile(data);
            } catch (err) {
                console.error("Error in company_profile event:", err);
            }
        });

        eventSource.addEventListener("market_data", (e) => {
            try {
                const data = JSON.parse(e.data);
                state.fullAnalysisData.market_data = data;
                appendLog("event", "Received Market Intelligence data");
                renderMarketData(data);
            } catch (err) {
                console.error("Error in market_data event:", err);
            }
        });

        eventSource.addEventListener("market_share", (e) => {
            try {
                const data = JSON.parse(e.data);
                state.fullAnalysisData.market_share = data;
                appendLog("event", "Received Market Share estimation");
                renderMarketShare(data);
            } catch (err) {
                console.error("Error in market_share event:", err);
            }
        });

        eventSource.addEventListener("local_competitors", (e) => {
            try {
                const data = JSON.parse(e.data);
                state.fullAnalysisData.local_competitors = data;
                appendLog("event", `Identified ${data.length} Direct Competitors`);
                renderCompetitorTier("localCompetitorsGrid", data, "local");
            } catch (err) {
                console.error("Error in local_competitors event:", err);
            }
        });

        eventSource.addEventListener("national_competitors", (e) => {
            try {
                const data = JSON.parse(e.data);
                state.fullAnalysisData.national_competitors = data;
                appendLog("event", `Identified ${data.length} National Competitors`);
                renderCompetitorTier("nationalCompetitorsGrid", data, "national");
            } catch (err) {
                console.error("Error in national_competitors event:", err);
            }
        });

        eventSource.addEventListener("global_competitors", (e) => {
            try {
                const data = JSON.parse(e.data);
                state.fullAnalysisData.global_competitors = data;
                appendLog("event", `Identified ${data.length} Global Competitors`);
                renderCompetitorTier("globalCompetitorsGrid", data, "global");
            } catch (err) {
                console.error("Error in global_competitors event:", err);
            }
        });

        eventSource.addEventListener("local_competitor_detailed_profile", (e) => {
            try {
                const data = JSON.parse(e.data);
                state.fullAnalysisData.local_competitors_detailed.push(data);
                appendLog("event", `Deep evaluation ready for: ${data.competitor_name || "Competitor"}`);
                updateDetailedCompetitorCard(data);
            } catch (err) {
                console.error("Error in local_competitor_detailed_profile event:", err);
            }
        });

        eventSource.addEventListener("swot_analysis", (e) => {
            try {
                const data = JSON.parse(e.data);
                state.fullAnalysisData.swot_analysis = data;
                appendLog("event", "Synthesized SWOT Analysis Matrix");
                renderSwotAnalysis(data);
            } catch (err) {
                console.error("Error in swot_analysis event:", err);
            }
        });

        eventSource.addEventListener("comparison_table", (e) => {
            try {
                const data = JSON.parse(e.data);
                state.fullAnalysisData.comparison_table = data;
                appendLog("event", "Generated Competitive Benchmark Table");
                renderComparisonTable(data);
            } catch (err) {
                console.error("Error in comparison_table event:", err);
            }
        });

        eventSource.addEventListener("surpass_recommendations", (e) => {
            try {
                const data = JSON.parse(e.data);
                state.fullAnalysisData.surpass_recommendations = data;
                appendLog("event", "Generated Surpass Recommendations Playbook");
                renderSurpassRecommendations(data);
            } catch (err) {
                console.error("Error in surpass_recommendations event:", err);
            }
        });

        eventSource.addEventListener("process_close", (e) => {
            try {
                const data = JSON.parse(e.data);
                appendLog("success", `Stream Finished: ${data.message || "Complete"}`);
            } catch (err) {
                appendLog("success", "Analysis pipeline completed successfully");
            }
            finishAnalysis();
        });

        eventSource.addEventListener("error", (e) => {
            try {
                if (e.data) {
                    const data = JSON.parse(e.data);
                    appendLog("error", `Error: ${data.message || "Unknown error"}`);
                    showError(data.message || "Analysis error encountered.");
                } else if (eventSource.readyState === EventSource.CLOSED) {
                    appendLog("info", "Stream connection closed");
                    finishAnalysis();
                }
            } catch (err) {
                console.error("SSE Error event:", err);
            }
        });

        eventSource.onerror = (err) => {
            console.warn("EventSource connection state:", eventSource.readyState);
            if (eventSource.readyState === EventSource.CLOSED) {
                finishAnalysis();
            }
        };
    }

    function finishAnalysis() {
        if (state.eventSource) {
            state.eventSource.close();
            state.eventSource = null;
        }
        state.isAnalyzing = false;
        if (elements.analyzeBtn) elements.analyzeBtn.disabled = false;
        if (elements.analyzeSpinner) elements.analyzeSpinner.style.display = "none";
        if (elements.btnIcon) elements.btnIcon.style.display = "inline-block";
        if (elements.btnText) elements.btnText.textContent = "Re-Analyze";

        updateProgress("Analysis 100% Complete!", 100, "step-strategy");
        setTimeout(() => {
            // keep progress visible or subtle
        }, 1000);
    }

    function showError(msg) {
        elements.errorMessage.textContent = msg;
        elements.errorBanner.style.display = "flex";
    }

    // ======================================================================
    // RENDERERS FOR ALL COMPLETE SECTIONS
    // ======================================================================

    // 1. Company Profile
    function renderCompanyProfile(p) {
        if (!p) return;
        const name = p.name || p.company_name || "Target Company";
        document.getElementById("companyName").textContent = name;
        document.getElementById("companyAvatar").textContent = name.substring(0, 2).toUpperCase();
        document.getElementById("companyCategory").textContent = p.category || "Enterprise";
        document.getElementById("companyLocation").textContent = p.location || "Global Presence";
        document.getElementById("companyFounded").textContent = p.founded_year ? `Est. ${p.founded_year}` : "Established";
        
        const tagline = p.tagline || p.description || "";
        document.getElementById("companyTagline").textContent = tagline;

        if (p.link) {
            document.getElementById("companyLink").href = p.link;
            document.getElementById("companyLinkText").textContent = p.link.replace(/^https?:\/\//, '');
        }

        // Elevator pitch
        const pitch = p.elevator_pitch || p.unique_value_proposition || p.description;
        if (pitch) {
            document.getElementById("elevatorPitchBox").style.display = "block";
            document.getElementById("elevatorPitchText").textContent = pitch;
        }

        // Core products/services
        const services = p.services || p.core_products_services || [];
        const servicesList = document.getElementById("coreServicesList");
        if (services.length > 0) {
            servicesList.innerHTML = services.map(s => `<span class="pill-item">${escapeHtml(s)}</span>`).join("");
        } else {
            servicesList.innerHTML = `<span class="pill-item">${escapeHtml(p.category || "Full Product Suite")}</span>`;
        }

        // Target industries
        const industries = p.industries || p.target_audience || [];
        const indList = document.getElementById("targetIndustriesList");
        if (Array.isArray(industries) && industries.length > 0) {
            indList.innerHTML = industries.map(i => `<span class="pill-item">${escapeHtml(i)}</span>`).join("");
        } else if (typeof industries === "string" && industries) {
            indList.innerHTML = `<span class="pill-item">${escapeHtml(industries)}</span>`;
        } else {
            indList.innerHTML = `<span class="pill-item">B2C & Global Retail</span>`;
        }

        // Tech stack
        const tech = p.technologies || [];
        const techList = document.getElementById("techStackList");
        if (tech.length > 0) {
            techList.innerHTML = tech.map(t => `<span class="tech-badge">${escapeHtml(t)}</span>`).join("");
        } else {
            techList.innerHTML = `<span class="tech-badge">Enterprise Cloud & Digital E-Commerce</span>`;
        }

        // Metadata
        const metaDetails = document.getElementById("companyMetaDetails");
        let metaHtml = "";
        if (p.team_size) metaHtml += `<div class="meta-row"><span class="meta-label">Team Size:</span><span class="meta-value">${escapeHtml(String(p.team_size))}</span></div>`;
        if (p.key_people && p.key_people.length) metaHtml += `<div class="meta-row"><span class="meta-label">Leadership:</span><span class="meta-value">${escapeHtml(p.key_people.join(", "))}</span></div>`;
        if (p.certifications && p.certifications.length) metaHtml += `<div class="meta-row"><span class="meta-label">Standards:</span><span class="meta-value">${escapeHtml(p.certifications.join(", "))}</span></div>`;
        if (p.awards && p.awards.length) metaHtml += `<div class="meta-row"><span class="meta-label">Awards:</span><span class="meta-value">${escapeHtml(p.awards.join(", "))}</span></div>`;
        
        metaDetails.innerHTML = metaHtml || `<div class="meta-row"><span class="meta-label">Status:</span><span class="meta-value">Active Industry Leader</span></div>`;
    }

    // 2. Market Data
    function renderMarketData(m) {
        if (!m) return;
        
        // Total Market Size
        let sizeVal = "--";
        if (typeof m.total_market_size === "object" && m.total_market_size !== null) {
            sizeVal = m.total_market_size.value || m.total_market_size.size || JSON.stringify(m.total_market_size);
        } else if (m.total_market_size) {
            sizeVal = String(m.total_market_size);
        }
        document.getElementById("marketSizeValue").textContent = sizeVal;
        document.getElementById("marketSector").textContent = m.sector || "Industry Market";

        // Growth rate
        let growthVal = "--";
        let periodVal = "CAGR Forecast";
        if (typeof m.growth_rate === "object" && m.growth_rate !== null) {
            growthVal = m.growth_rate.cagr || m.growth_rate.rate || m.growth_rate.value || "--";
            periodVal = m.growth_rate.period || m.growth_rate.forecast || "Projected";
        } else if (m.growth_rate) {
            growthVal = String(m.growth_rate);
        }
        document.getElementById("marketGrowthRate").textContent = growthVal;
        document.getElementById("growthPeriod").textContent = periodVal;

        // Key drivers
        const drivers = m.key_drivers || [];
        const driversList = document.getElementById("marketDriversList");
        if (drivers.length > 0) {
            driversList.innerHTML = drivers.map(d => `<li>${escapeHtml(d)}</li>`).join("");
        }

        // Major regions
        const regions = m.major_regions || [];
        const regionsList = document.getElementById("marketRegionsList");
        if (regions.length > 0) {
            regionsList.innerHTML = regions.map(r => `<span class="pill-item">${escapeHtml(r)}</span>`).join("");
        }

        // Market news
        if (m.news_summary) {
            document.getElementById("marketNewsSummary").textContent = m.news_summary;
        }
    }

    // 3. Market Share
    // 3. Market Share
    function renderMarketShare(s) {
        if (!s) return;
        
        let captureVal = "--";
        let confidence = "";
        let basis = "";
        if (s.market_capture) {
            if (typeof s.market_capture === "object") {
                const pct = s.market_capture.percentage ?? s.market_capture.share ?? s.market_capture.estimate;
                captureVal = pct !== undefined ? (typeof pct === 'number' ? `${pct}%` : String(pct)) : "--";
                confidence = s.market_capture.confidence_level ? ` (${s.market_capture.confidence_level} confidence)` : "";
                basis = s.market_capture.basis || "";
            } else {
                captureVal = String(s.market_capture);
            }
        }
        document.getElementById("marketCaptureValue").textContent = `${captureVal}${confidence}`;

        let posVal = "Strong Competitor";
        if (s.current_position) {
            if (typeof s.current_position === "object") {
                if (s.current_position.ranking || s.current_position.status) {
                    posVal = s.current_position.ranking || s.current_position.status;
                } else if (Array.isArray(s.current_position.strengths) && s.current_position.strengths.length > 0) {
                    posVal = "Market Leader";
                }
            } else {
                posVal = String(s.current_position);
            }
        }
        document.getElementById("marketPositionValue").textContent = posVal;

        // Growth opportunities: parse vertical and horizontal scaling
        const oppsList = document.getElementById("growthOpportunitiesList");
        let opps = [];
        if (s.growth_recommendations) {
            if (typeof s.growth_recommendations === "object") {
                if (Array.isArray(s.growth_recommendations.vertical_scaling)) {
                    s.growth_recommendations.vertical_scaling.forEach(item => {
                        if (typeof item === "string") {
                            opps.push(item);
                        } else if (item && typeof item === "object") {
                            const strat = item.strategy || "Vertical Focus";
                            const desc = item.description ? ` - ${item.description}` : "";
                            const impact = item.potential_impact ? ` <span class="badge-impact-${item.potential_impact.toLowerCase().includes('high') ? 'high' : 'med'}">${escapeHtml(item.potential_impact.toUpperCase())} IMPACT</span>` : "";
                            opps.push(`<strong>${escapeHtml(strat)}</strong>${escapeHtml(desc)}${impact}`);
                        }
                    });
                }
                if (Array.isArray(s.growth_recommendations.horizontal_scaling)) {
                    s.growth_recommendations.horizontal_scaling.forEach(item => {
                        if (typeof item === "string") {
                            opps.push(item);
                        } else if (item && typeof item === "object") {
                            const strat = item.strategy || "Horizontal Expansion";
                            const desc = item.description ? ` - ${item.description}` : "";
                            const impact = item.potential_impact ? ` <span class="badge-impact-${item.potential_impact.toLowerCase().includes('high') ? 'high' : 'med'}">${escapeHtml(item.potential_impact.toUpperCase())} IMPACT</span>` : "";
                            opps.push(`<strong>${escapeHtml(strat)}</strong>${escapeHtml(desc)}${impact}`);
                        }
                    });
                }
                if (Array.isArray(s.growth_recommendations.opportunities)) {
                    s.growth_recommendations.opportunities.forEach(o => opps.push(escapeHtml(typeof o === 'string' ? o : JSON.stringify(o))));
                }
            } else if (Array.isArray(s.growth_recommendations)) {
                s.growth_recommendations.forEach(o => opps.push(escapeHtml(typeof o === 'string' ? o : JSON.stringify(o))));
            }
        }
        if (Array.isArray(s.growth_opportunities) && s.growth_opportunities.length > 0) {
            s.growth_opportunities.forEach(o => opps.push(escapeHtml(typeof o === 'string' ? o : JSON.stringify(o))));
        }
        if (opps.length > 0) {
            oppsList.innerHTML = opps.map(o => `<li>${o}</li>`).join("");
        } else {
            oppsList.innerHTML = `<li>Continuous capability scaling and market penetration</li>`;
        }

        // Threats / challenges
        let challenges = [];
        if (s.current_position?.challenges && Array.isArray(s.current_position.challenges)) {
            s.current_position.challenges.forEach(c => challenges.push(escapeHtml(typeof c === 'string' ? c : JSON.stringify(c))));
        }
        if (s.threats_to_share && Array.isArray(s.threats_to_share)) {
            s.threats_to_share.forEach(c => challenges.push(escapeHtml(typeof c === 'string' ? c : JSON.stringify(c))));
        }
        if (s.challenges && Array.isArray(s.challenges)) {
            s.challenges.forEach(c => challenges.push(escapeHtml(typeof c === 'string' ? c : JSON.stringify(c))));
        }
        if (basis) {
            challenges.push(`<strong>Estimation Basis:</strong> ${escapeHtml(basis)}`);
        }
        const challList = document.getElementById("industryChallengesList");
        if (challenges.length > 0) {
            challList.innerHTML = challenges.map(c => `<li>${c}</li>`).join("");
        } else {
            challList.innerHTML = `<li>Competitive pricing pressure and evolving consumer trends</li>`;
        }
    }

    // 4. Competitor Lists
    function renderCompetitorTier(containerId, list, tier) {
        const container = document.getElementById(containerId);
        if (!container) return;

        if (!list || list.length === 0) {
            container.innerHTML = `<div class="empty-state">No ${tier} competitors found.</div>`;
            return;
        }

        container.innerHTML = list.map((c, idx) => {
            const name = c.competitor_name || c.name || `Competitor ${idx + 1}`;
            const desc = c.description || "Leading industry competitor.";
            const link = c.link || c.website || "#";
            const linkHtml = link !== "#" ? `<a href="${link}" target="_blank" class="comp-link">Visit Website &rarr;</a>` : "";

            return `
                <div class="competitor-card" id="comp-card-${slugify(name)}">
                    <div>
                        <div class="comp-header">
                            <h4 class="comp-name">${escapeHtml(name)}</h4>
                            <span class="comp-badge at-par">Detected</span>
                        </div>
                        <p class="comp-desc">${escapeHtml(desc)}</p>
                    </div>
                    <div>
                        ${linkHtml}
                    </div>
                </div>
            `;
        }).join("");
    }

    // 5. Update Local Competitor with Deep-Dive Details
    function updateDetailedCompetitorCard(detail) {
        const name = detail.competitor_name || "Unknown";
        const cardId = `comp-card-${slugify(name)}`;
        let card = document.getElementById(cardId);

        const summary = detail.comparison?.summary || "at-par";
        const badgeClass = summary.toLowerCase().replace(/\s+/g, '-');
        const badgeLabel = summary.toUpperCase();

        let fieldComparisonsHtml = "";
        if (detail.comparison?.field_comparison) {
            const fields = detail.comparison.field_comparison;
            fieldComparisonsHtml = '<div class="comp-field-compare">';
            for (const [key, val] of Object.entries(fields)) {
                fieldComparisonsHtml += `
                    <div class="comp-compare-item">
                        <span>${escapeHtml(formatKey(key))}:</span>
                        <span>${escapeHtml(String(val))}</span>
                    </div>
                `;
            }
            fieldComparisonsHtml += '</div>';
        }

        const profileDesc = detail.profile?.description || detail.description || "";
        const link = detail.link || "#";

        const innerContent = `
            <div>
                <div class="comp-header">
                    <h4 class="comp-name">${escapeHtml(name)}</h4>
                    <span class="comp-badge ${badgeClass}">${escapeHtml(badgeLabel)}</span>
                </div>
                <p class="comp-desc">${escapeHtml(profileDesc)}</p>
                ${fieldComparisonsHtml}
            </div>
            <div>
                ${link !== "#" ? `<a href="${link}" target="_blank" class="comp-link">Explore Site &rarr;</a>` : ""}
            </div>
        `;

        if (card) {
            card.innerHTML = innerContent;
        } else {
            // Append if not exists
            const grid = document.getElementById("localCompetitorsGrid");
            if (grid) {
                const newCard = document.createElement("div");
                newCard.className = "competitor-card";
                newCard.id = cardId;
                newCard.innerHTML = innerContent;
                grid.appendChild(newCard);
            }
        }
    }

    // 6. SWOT Analysis
    function renderSwotAnalysis(swot) {
        if (!swot) return;
        const matrix = swot.swot_analysis || swot;

        // Support both schemas:
        // 1) matrix.our_company.swot: { strengths, weaknesses, opportunities, threats }
        // 2) matrix.our_company: { strengths, weaknesses, opportunities, threats }
        // 3) matrix: { strengths, weaknesses, opportunities, threats }
        const target = matrix.our_company?.swot || matrix.our_company || matrix;

        const populateList = (elementId, items) => {
            const el = document.getElementById(elementId);
            if (!el) return;
            if (Array.isArray(items) && items.length > 0) {
                el.innerHTML = items.map(i => {
                    const text = typeof i === "string" ? i : (i.point || i.description || JSON.stringify(i));
                    return `<li>${escapeHtml(text)}</li>`;
                }).join("");
            } else if (typeof items === "string" && items) {
                el.innerHTML = `<li>${escapeHtml(items)}</li>`;
            } else {
                el.innerHTML = `<li>No items identified.</li>`;
            }
        };

        populateList("swotStrengthsList", target.strengths || target.Strengths);
        populateList("swotWeaknessesList", target.weaknesses || target.Weaknesses);
        populateList("swotOpportunitiesList", target.opportunities || target.Opportunities);
        populateList("swotThreatsList", target.threats || target.Threats);
    }

    // 7. Comparison Table
    function renderComparisonTable(data) {
        const container = document.getElementById("comparisonTableContainer");
        if (!container || !data) return;

        const tableData = data.comparison_table || data;

        const formatVal = (val) => {
            if (val === undefined || val === null || val === "") return "-";
            if (Array.isArray(val)) {
                if (val.length === 0) return "-";
                return `<ul>${val.map(item => `<li>${escapeHtml(typeof item === 'string' ? item : JSON.stringify(item))}</li>`).join("")}</ul>`;
            }
            if (typeof val === "object") {
                const entries = Object.entries(val);
                if (entries.length === 0) return "-";
                return `<ul>${entries.map(([k, v]) => `<li><strong>${escapeHtml(formatKey(k))}:</strong> ${escapeHtml(typeof v === 'object' ? JSON.stringify(v) : String(v))}</li>`).join("")}</ul>`;
            }
            return escapeHtml(String(val));
        };

        // Check if structure is: { our_company: {...}, competitors: [{ competitor_name: "...", details: {...} }] }
        if (tableData.our_company || Array.isArray(tableData.competitors)) {
            const ourCo = tableData.our_company || {};
            const comps = Array.isArray(tableData.competitors) ? tableData.competitors : [];

            const ourName = ourCo.name || ourCo.company_name || state.fullAnalysisData.company_profile?.name || "Our Company";

            // Headers
            let html = '<table class="benchmark-table"><thead><tr>';
            html += `<th>Benchmark Dimension</th>`;
            html += `<th style="background: var(--surface-3); border-left: 2px solid var(--accent); color: var(--accent);">${escapeHtml(ourName)} (Target)</th>`;
            comps.forEach(c => {
                const compName = c.competitor_name || c.name || "Competitor";
                html += `<th>${escapeHtml(compName)}</th>`;
            });
            html += '</tr></thead><tbody>';

            // Comparison dimensions
            const dimensions = [
                { key: "description", label: "Overview & Description", ourVal: ourCo.description },
                { key: "services", label: "Products & Core Services", ourVal: ourCo.services || ourCo.core_products_services },
                { key: "technologies", label: "Tech Stack & Innovation", ourVal: ourCo.technologies },
                { key: "industries", label: "Market Segments & Audience", ourVal: ourCo.industries || ourCo.target_audience },
                { key: "team_size", label: "Scale & Team Size", ourVal: ourCo.team_size },
                { key: "strengths", label: "Core Competitive Strengths", ourVal: ourCo.strengths },
                { key: "weaknesses", label: "Weaknesses / Gaps", ourVal: ourCo.weaknesses },
                { key: "pricing_strategy", label: "Pricing / Go-To-Market", ourVal: ourCo.pricing_strategy },
                { key: "recent_achievements", label: "Recent Achievements", ourVal: ourCo.recent_achievements || ourCo.awards }
            ];

            dimensions.forEach(dim => {
                html += `<tr>`;
                html += `<td><strong>${escapeHtml(dim.label)}</strong></td>`;
                html += `<td style="background: rgba(198, 242, 78, 0.05); border-left: 2px solid var(--accent);">${formatVal(dim.ourVal)}</td>`;
                comps.forEach(c => {
                    const details = c.details || c;
                    const val = details[dim.key] !== undefined ? details[dim.key] : (c[dim.key]);
                    html += `<td>${formatVal(val)}</td>`;
                });
                html += `</tr>`;
            });

            html += '</tbody></table>';
            container.innerHTML = html;
            return;
        }

        // Standard columns and rows format
        if (tableData.columns && tableData.rows) {
            let html = '<table class="benchmark-table"><thead><tr>';
            tableData.columns.forEach(col => {
                html += `<th>${escapeHtml(col)}</th>`;
            });
            html += '</tr></thead><tbody>';

            tableData.rows.forEach(row => {
                html += '<tr>';
                if (Array.isArray(row)) {
                    row.forEach(cell => {
                        html += `<td>${formatVal(cell)}</td>`;
                    });
                } else if (typeof row === "object") {
                    tableData.columns.forEach(col => {
                        html += `<td>${formatVal(row[col])}</td>`;
                    });
                }
                html += '</tr>';
            });

            html += '</tbody></table>';
            container.innerHTML = html;
            return;
        }

        // Array of comparison objects
        if (Array.isArray(tableData) && tableData.length > 0) {
            const keys = Object.keys(tableData[0]);
            let html = '<table class="benchmark-table"><thead><tr>';
            keys.forEach(k => { html += `<th>${escapeHtml(formatKey(k))}</th>`; });
            html += '</tr></thead><tbody>';

            tableData.forEach(item => {
                html += '<tr>';
                keys.forEach(k => {
                    html += `<td>${formatVal(item[k])}</td>`;
                });
                html += '</tr>';
            });
            html += '</tbody></table>';
            container.innerHTML = html;
            return;
        }

        // Dict / key-value matrix
        if (typeof tableData === "object" && tableData !== null) {
            let html = '<table class="benchmark-table"><thead><tr><th>Evaluation Metric</th><th>Benchmark Analysis</th></tr></thead><tbody>';
            for (const [k, v] of Object.entries(tableData)) {
                html += `<tr><td>${escapeHtml(formatKey(k))}</td><td>${formatVal(v)}</td></tr>`;
            }
            html += '</tbody></table>';
            container.innerHTML = html;
            return;
        }

        container.innerHTML = `<div class="empty-state">No comparison table structured.</div>`;
    }

    // 8. Surpass Recommendations
    function renderSurpassRecommendations(recData) {
        const container = document.getElementById("surpassStrategiesContainer");
        if (!container || !recData) return;

        const recs = recData.recommendations || recData.strategies || (Array.isArray(recData) ? recData : []);

        if (Array.isArray(recs) && recs.length > 0) {
            container.innerHTML = recs.map((item, idx) => {
                let title = `Strategy #${idx + 1}`;
                let actionsHtml = "";

                if (typeof item === "string") {
                    actionsHtml = `<p class="strat-desc">${escapeHtml(item)}</p>`;
                } else if (typeof item === "object" && item !== null) {
                    if (item.competitor && Array.isArray(item.actions)) {
                        title = `Actionable Blueprint to Surpass ${escapeHtml(item.competitor)}`;
                        actionsHtml = `
                            <ul class="strat-actions">
                                ${item.actions.map(act => `<li>${escapeHtml(typeof act === "string" ? act : JSON.stringify(act))}</li>`).join("")}
                            </ul>
                        `;
                    } else if (item.title || item.initiative || item.action) {
                        title = item.title || item.initiative || item.action;
                        const desc = item.description || item.detail || item.rationale || "";
                        actionsHtml = desc ? `<p class="strat-desc">${escapeHtml(desc)}</p>` : "";
                        if (Array.isArray(item.actions)) {
                            actionsHtml += `
                                <ul class="strat-actions">
                                    ${item.actions.map(act => `<li>${escapeHtml(typeof act === "string" ? act : JSON.stringify(act))}</li>`).join("")}
                                </ul>
                            `;
                        }
                    } else if (Array.isArray(item.actions)) {
                        title = `Tactical Playbook #${idx + 1}`;
                        actionsHtml = `
                            <ul class="strat-actions">
                                ${item.actions.map(act => `<li>${escapeHtml(typeof act === "string" ? act : JSON.stringify(act))}</li>`).join("")}
                            </ul>
                        `;
                    } else {
                        // Dict with details
                        title = item.name || item.strategy || `Strategic Move #${idx + 1}`;
                        const details = Object.entries(item).filter(([k]) => !['name', 'strategy', 'title'].includes(k));
                        actionsHtml = `
                            <ul class="strat-actions">
                                ${details.map(([k, v]) => `<li><strong>${escapeHtml(formatKey(k))}:</strong> ${escapeHtml(typeof v === 'object' ? JSON.stringify(v) : String(v))}</li>`).join("")}
                            </ul>
                        `;
                    }
                }

                return `
                    <div class="strategy-card">
                        <div class="strategy-number">${idx + 1}</div>
                        <div class="strategy-body">
                            <h4 class="strat-title">${title}</h4>
                            ${actionsHtml}
                        </div>
                    </div>
                `;
            }).join("");
            return;
        }

        // If dict with sections
        if (typeof recData === "object" && recData !== null) {
            let html = "";
            let idx = 1;
            for (const [category, content] of Object.entries(recData)) {
                let contentHtml = "";
                if (Array.isArray(content)) {
                    contentHtml = `
                        <ul class="strat-actions">
                            ${content.map(c => `<li>${escapeHtml(typeof c === 'string' ? c : JSON.stringify(c))}</li>`).join("")}
                        </ul>
                    `;
                } else {
                    contentHtml = `<p class="strat-desc">${escapeHtml(typeof content === "object" ? JSON.stringify(content, null, 2) : String(content))}</p>`;
                }

                html += `
                    <div class="strategy-card">
                        <div class="strategy-number">${idx++}</div>
                        <div class="strategy-body">
                            <h4 class="strat-title">${escapeHtml(formatKey(category))}</h4>
                            ${contentHtml}
                        </div>
                    </div>
                `;
            }
            container.innerHTML = html;
            return;
        }

        container.innerHTML = `<div class="empty-state">No surpass strategies available.</div>`;
    }

    // ======================================================================
    // UTILITY HELPERS
    // ======================================================================
    function escapeHtml(str) {
        if (!str) return "";
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function formatKey(key) {
        return key.replace(/_/g, " ").replace(/\b\w/g, l => l.toUpperCase());
    }

    function slugify(text) {
        return text.toString().toLowerCase()
            .replace(/\s+/g, '-')
            .replace(/[^\w\-]+/g, '')
            .replace(/\-\-+/g, '-')
            .replace(/^-+/, '')
            .replace(/-+$/, '');
    }
});
