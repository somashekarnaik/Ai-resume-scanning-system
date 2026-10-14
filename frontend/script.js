const API_URL = (import.meta.env.VITE_API_URL || "").replace(/\/+$/, "");
let cameraStream = null;
let capturedPhotoFile = null;

function apiUrl(path) {
    return `${API_URL}${path}`;
}

async function checkBackend() {
    try {
        const response = await fetch(apiUrl("/health"));
        if (!response.ok) {
            throw new Error(`Backend health check failed with status ${response.status}.`);
        }
    } catch (error) {
        console.error("Backend is not running:", error);
    }
}

function showMessage(elementId, message, isError = false) {
    const element = document.getElementById(elementId);
    if (!element) return;

    element.textContent = message;
    element.style.color = isError ? "#c62828" : "#1e7e34";
}

function getAuthenticatedUser() {
    try {
        const user = JSON.parse(localStorage.getItem("user") || "null");
        return user && user.user_id ? user : null;
    } catch (error) {
        console.error("Could not read the saved login session:", error);
        return null;
    }
}

async function registerUser(event) {
    event.preventDefault();

    const name = document.getElementById("registerName")?.value.trim();
    const email = document.getElementById("registerEmail")?.value.trim();
    const password = document.getElementById("registerPassword")?.value.trim();

    if (!name || !email || !password) {
        showMessage("registerMessage", "Please fill in all fields.", true);
        return;
    }

    try {
        const response = await fetch(apiUrl("/api/auth/register"), {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ name, email, password }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Registration failed.");
        }

        showMessage("registerMessage", "Registration successful! Redirecting to login...");

        setTimeout(() => {
            window.location.href = "login.html";
        }, 1200);
    } catch (error) {
        console.error(error);
        showMessage("registerMessage", error.message || "Registration failed.", true);
    }
}

async function loginUser(event) {
    event.preventDefault();

    const email = document.getElementById("loginEmail")?.value.trim();
    const password = document.getElementById("loginPassword")?.value.trim();

    if (!email || !password) {
        showMessage("loginMessage", "Please enter your email and password.", true);
        return;
    }

    try {
        const response = await fetch(apiUrl("/api/auth/login"), {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ email, password }),
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Login failed.");
        }

        localStorage.setItem("user", JSON.stringify({
            user_id: data.user_id,
            name: data.name,
            email,
        }));
        localStorage.setItem("user_name", data.name);

        showMessage("loginMessage", "Login successful! Redirecting...");

        setTimeout(() => {
            window.location.href = "upload-resume.html";
        }, 800);
    } catch (error) {
        console.error(error);
        showMessage("loginMessage", error.message || "Login failed.", true);
    }
}

function showUploadMessage(message, isError = false) {
    const uploadMessage = document.getElementById("uploadMessage");
    if (!uploadMessage) return;

    uploadMessage.textContent = message;
    uploadMessage.style.color = isError ? "#c62828" : "#1e7e34";
}

let currentTailoredResumeBase64 = "";
function populateResultList(containerId, items, itemClass = "") {
    const container = document.getElementById(containerId);
    if (!container) return;

    container.replaceChildren();
    if (!items.length) {
        const emptyState = document.createElement(
            container.tagName === "UL" ? "li" : "p"
        );
        emptyState.textContent = "None detected.";
        container.append(emptyState);
        return;
    }

    items.forEach((item) => {
        const entry = document.createElement(itemClass ? "span" : "li");
        if (itemClass) entry.className = itemClass;
        entry.textContent = item;
        container.append(entry);
    });
}

function displayJobMatches(data) {
    const section = document.getElementById("jobMatches");
    const summary = document.getElementById("jobMatchesSummary");
    const list = document.getElementById("jobMatchesList");
    const sampleSection = document.getElementById("sampleResumeSection");
    const sampleRole = document.getElementById("sampleResumeRole");
    const sampleText = document.getElementById("sampleResumeText");
    const recommendationReason = document.getElementById("recommendationReason");
    const formatReview = document.getElementById("formatReview");
    const formatIssues = document.getElementById("formatIssues");
    const formatReviewNote = document.getElementById("formatReviewNote");
    const downloadButton = document.getElementById("downloadSampleResume");
    if (
        !section || !summary || !list || !sampleSection || !sampleRole ||
        !sampleText || !recommendationReason || !formatReview ||
        !formatIssues || !formatReviewNote || !downloadButton
    ) return;

    const jobs = data.matching_jobs || [];
    list.replaceChildren();
    section.hidden = false;
    sampleSection.hidden = true;
    formatReview.hidden = true;
    currentTailoredResumeBase64 = "";

    summary.textContent =
        `Expected role: ${data.expected_role} — ${data.expected_role_score}% skills match ` +
        `(a ${data.expected_role_match_threshold}% match is the target). ` +
        `Recommended role: ${data.recommended_job.title}.`;
    recommendationReason.textContent = data.recommendation_reason;

    jobs.slice(0, 3).forEach((job) => {
        const card = document.createElement("article");
        card.className = "job-match-card";

        const title = document.createElement("h3");
        title.textContent = job.title;

        const company = document.createElement("p");
        company.className = "job-match-company";
        company.textContent = job.company;

        const score = document.createElement("p");
        score.className = "job-match-score";
        score.textContent = `${job.match_score}% skills match`;

        const skills = document.createElement("p");
        skills.textContent = job.matched_skills.length
            ? `Matching skills: ${job.matched_skills.join(", ")}`
            : "No listed skills matched.";

        card.append(title, company, score, skills);
        list.append(card);
    });

    if (data.recommended_job && data.tailored_resume_docx_base64) {
        sampleRole.textContent = data.recommended_job.title;
        sampleText.textContent = data.resume_preview || "Preview is unavailable.";
        currentTailoredResumeBase64 = data.tailored_resume_docx_base64;
        sampleSection.hidden = false;
    }

    const issues = data.format_review?.issues || [];
    formatIssues.replaceChildren();
    if (issues.length) {
        issues.forEach((issue) => {
            const item = document.createElement("li");
            item.textContent = issue;
            formatIssues.append(item);
        });
    } else {
        const item = document.createElement("li");
        item.textContent = "No common text-structure issues were detected.";
        formatIssues.append(item);
    }
    formatReviewNote.textContent = data.format_review?.note || "";
    formatReview.hidden = false;

    const overallScore = document.getElementById("overallScore");
    const skillScore = document.getElementById("skillScore");
    const similarityScore = document.getElementById("similarityScore");
    if (overallScore) overallScore.textContent = `${Number(data.overall_score || 0).toFixed(1)}%`;
    if (skillScore) skillScore.textContent = `${Number(data.skill_score || 0).toFixed(1)}%`;
    if (similarityScore) similarityScore.textContent = `${Number(data.similarity_score || 0).toFixed(1)}%`;
    populateResultList("detectedSkills", data.resume_skills || [], "skill");
    populateResultList("matchedSkills", data.matched_skills || [], "skill");
    populateResultList("missingSkills", data.missing_skills || [], "skill missing");
    populateResultList("recommendations", data.recommendations || []);
}

function downloadTailoredResume(button) {
    if (!currentTailoredResumeBase64) return;

    const binary = atob(currentTailoredResumeBase64);
    const bytes = Uint8Array.from(binary, (character) => character.charCodeAt(0));
    const blob = new Blob([bytes], {
        type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "tailored-resume.docx";
    link.click();
    URL.revokeObjectURL(url);
}

function logoutUser() {
    localStorage.removeItem("user");
    localStorage.removeItem("user_id");
    localStorage.removeItem("user_name");
    localStorage.removeItem("resume_result");
    sessionStorage.removeItem("resumeAnalysisResult");
    window.location.href = "login.html";
}

async function findJobs(event) {
    if (event && event.preventDefault) event.preventDefault();
    const input = document.getElementById("userSkills");
    const container = document.getElementById("jobs");
    if (!input || !container) return;

    const skills = input.value.trim();
    if (!skills) {
        alert("Please enter at least one skill (e.g. Python, SQL, React).");
        return;
    }

    container.innerHTML = `
        <div class="job-card" style="text-align: center; color: #5b6475;">
            <p>Scanning job roles for matching skills...</p>
        </div>
    `;

    try {
        const response = await fetch(apiUrl("/api/jobs/match"), {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ skills }),
        });

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.detail || "Failed to find matching jobs.");
        }

        const jobs = await response.json();
        container.replaceChildren();

        if (!jobs || !jobs.length) {
            container.innerHTML = `
                <div class="job-card">
                    <p>No matching jobs found for those skills. Try adding skills like Python, SQL, React, Machine Learning, or Excel.</p>
                </div>
            `;
            return;
        }

        jobs.forEach((job) => {
            const card = document.createElement("article");
            card.className = "job-card";
            card.innerHTML = `
                <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 8px;">
                    <div>
                        <h3 style="font-size: 20px; color: #182848; margin-bottom: 4px;">${job.title}</h3>
                        <p class="job-match-company" style="font-weight: 500;">${job.company || "Company Partner"}</p>
                    </div>
                    <span class="job-match-score" style="font-size: 16px; background: #e7f0ff; padding: 6px 14px; border-radius: 20px;">
                        ${job.match_score}% match
                    </span>
                </div>
                <div style="margin-top: 14px;">
                    <p style="font-size: 14px; color: #334155; margin-bottom: 8px;"><strong>Matched Skills:</strong></p>
                    <div>
                        ${job.matched_skills && job.matched_skills.length
                            ? job.matched_skills.map(s => `<span class="skill" style="font-size: 13px;">${s}</span>`).join(" ")
                            : "<span style='color: #64748b; font-size: 14px;'>No direct overlap with listed role requirements</span>"}
                    </div>
                </div>
            `;
            container.append(card);
        });
    } catch (error) {
        console.error("Job matching error:", error);
        container.innerHTML = `
            <div class="job-card" style="border-left: 4px solid #c62828;">
                <p style="color: #c62828; font-weight: bold;">Could not complete job search</p>
                <p style="color: #64748b; font-size: 14px; margin-top: 4px;">${error.message || "Please check connection to the backend."}</p>
            </div>
        `;
    }
}

window.findJobs = findJobs;
window.logoutUser = logoutUser;
window.logout = logoutUser;


async function loadJobRoles(roleSelect, jobDescription) {
    try {
        const response = await fetch(apiUrl("/api/jobs/roles"));
        const roles = await response.json();
        if (!response.ok || !Array.isArray(roles) || !roles.length) {
            throw new Error("The sample job descriptions could not be loaded.");
        }

        const selectedTitle = roleSelect.value || "Python Developer";
        roleSelect.replaceChildren();
        roles.forEach((role) => {
            const option = document.createElement("option");
            option.value = role.title;
            option.textContent = role.title;
            roleSelect.append(option);
        });
        roleSelect.value = roles.some((role) => role.title === selectedTitle)
            ? selectedTitle
            : roles[0].title;

        const updateDescription = () => {
            const selectedRole = roles.find((role) => role.title === roleSelect.value);
            if (selectedRole) {
                jobDescription.value = selectedRole.description;
            }
        };
        roleSelect.addEventListener("change", updateDescription);
        updateDescription();
    } catch (error) {
        console.error("Could not load job role descriptions:", error);
        jobDescription.value = "";
        showUploadMessage(
            "Could not load the sample job descriptions. You can still enter a job description manually.",
            true
        );
    }
}

async function startCamera() {
    const video = document.getElementById("cameraPreview");
    const photoInput = document.getElementById("photoUpload");
    const captureButton = document.getElementById("capturePhotoButton");

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        alert("Camera access is not supported on this browser. Please upload a photo instead.");
        photoInput.click();
        return;
    }

    try {
        cameraStream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: "environment" },
            audio: false,
        });

        video.srcObject = cameraStream;
        video.hidden = false;
        captureButton.classList.remove("hidden");
        showUploadMessage("Camera ready. Capture a photo or choose a file from your device.");
    } catch (error) {
        console.error("Camera access denied:", error);
        showUploadMessage("Camera access was blocked. You can still upload a photo manually.", true);
        photoInput.click();
    }
}

function stopCamera() {
    if (cameraStream) {
        cameraStream.getTracks().forEach((track) => track.stop());
        cameraStream = null;
    }

    const video = document.getElementById("cameraPreview");
    if (video) {
        video.srcObject = null;
        video.hidden = true;
    }

    const captureButton = document.getElementById("capturePhotoButton");
    if (captureButton) {
        captureButton.classList.add("hidden");
    }
}

function capturePhoto() {
    const video = document.getElementById("cameraPreview");
    const canvas = document.getElementById("photoCanvas");
    const preview = document.getElementById("photoPreview");
    const previewWrapper = document.getElementById("photoPreviewWrapper");

    if (!video || !canvas || !preview) {
        return;
    }

    const context = canvas.getContext("2d");
    canvas.width = video.videoWidth || 640;
    canvas.height = video.videoHeight || 480;
    context.drawImage(video, 0, 0, canvas.width, canvas.height);

    canvas.toBlob((blob) => {
        if (!blob) return;

        capturedPhotoFile = new File([blob], `camera-photo-${Date.now()}.png`, {
            type: "image/png",
        });

        const dataUrl = URL.createObjectURL(blob);
        preview.src = dataUrl;
        previewWrapper.hidden = false;
        showUploadMessage("Photo captured successfully.");
        stopCamera();
    }, "image/png");
}

function handlePhotoUpload(event) {
    const file = event.target.files && event.target.files[0];
    const preview = document.getElementById("photoPreview");
    const previewWrapper = document.getElementById("photoPreviewWrapper");

    if (!file) return;

    capturedPhotoFile = file;
    const reader = new FileReader();
    reader.onload = function (e) {
        preview.src = e.target.result;
        previewWrapper.hidden = false;
        showUploadMessage(`Photo selected: ${file.name}`);
    };
    reader.readAsDataURL(file);
}

async function uploadResume() {
    const fileInput = document.getElementById("resumeFile");
    const analyzeButton = document.getElementById("analyzeResumeButton");
    const user = getAuthenticatedUser();

    if (!user) {
        showUploadMessage("Please log in before uploading a resume.", true);
        window.location.href = "login.html";
        return;
    }

    if (!fileInput || !fileInput.files.length) {
        alert("Please select a resume first.");
        return;
    }

    const file = fileInput.files[0];
    const jobDescription = document.getElementById("jobDescription");
    const formData = new FormData();
    const expectedRole = document.getElementById("expectedJobRole");

    formData.append("file", file);
    formData.append("job_description", jobDescription ? jobDescription.value : "");
    formData.append("expected_role", expectedRole ? expectedRole.value : "Python Developer");
    formData.append("user_id", String(user.user_id));

    if (capturedPhotoFile) {
        formData.append("photo", capturedPhotoFile, capturedPhotoFile.name);
    }

    try {
        if (analyzeButton) {
            analyzeButton.disabled = true;
            analyzeButton.textContent = "Analyzing...";
        }
        const response = await fetch(apiUrl("/api/resume/upload"), {
            method: "POST",
            body: formData,
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.detail || "Upload failed");
        }

        try {
            sessionStorage.setItem("resumeAnalysisResult", JSON.stringify(data));
            localStorage.setItem("resume_result", JSON.stringify(data));
        } catch (storageError) {
            throw new Error("The analysis is ready, but could not be saved for the results page. Please try again.");
        }
        window.location.href = "resume-result.html";
    } catch (error) {
        console.error(error);
        showUploadMessage(error.message || "Could not connect to the backend.", true);
        alert(error.message || "Could not connect to the backend.");
    } finally {
        if (analyzeButton) {
            analyzeButton.disabled = false;
            analyzeButton.textContent = "Analyze Resume";
        }
    }
}

document.addEventListener("DOMContentLoaded", () => {
    if (document.body.dataset.entryGate === "true") {
        window.location.replace(
            getAuthenticatedUser() ? "upload-resume.html" : "register.html"
        );
        return;
    }

    if (
        document.body.dataset.authRequired === "true" &&
        !getAuthenticatedUser()
    ) {
        window.location.replace("register.html");
        return;
    }

    checkBackend();

    // Sync dashboard profile and stats if available
    const authUser = getAuthenticatedUser();
    const userNameEl = document.getElementById("userName");
    if (userNameEl && authUser) {
        userNameEl.textContent = authUser.name || "User";
    }

    const savedResumeResult = localStorage.getItem("resume_result");
    if (savedResumeResult) {
        try {
            const parsed = JSON.parse(savedResumeResult);
            const resumeScoreEl = document.getElementById("resumeScore");
            const skillsCountEl = document.getElementById("skillsCount");
            const jobsCountEl = document.getElementById("jobsCount");
            if (resumeScoreEl && parsed.overall_score !== undefined) {
                resumeScoreEl.textContent = `${Number(parsed.overall_score).toFixed(1)}%`;
            }
            if (skillsCountEl && parsed.resume_skills) {
                skillsCountEl.textContent = parsed.resume_skills.length;
            }
            if (jobsCountEl && parsed.matched_skills) {
                jobsCountEl.textContent = parsed.matched_skills.length;
            }
        } catch (e) {
            console.error("Could not parse saved resume result:", e);
        }
    }

    // Attach logout handlers
    document.querySelectorAll(".logout-btn, #logoutButton, a[href*='logout']").forEach((btn) => {
        btn.addEventListener("click", (e) => {
            e.preventDefault();
            logoutUser();
        });
    });

    // Attach findJobs handlers
    const findJobsBtn = document.getElementById("findJobsButton") || document.querySelector("button[onclick*='findJobs']");
    if (findJobsBtn) {
        findJobsBtn.addEventListener("click", findJobs);
    }
    const userSkillsInput = document.getElementById("userSkills");
    if (userSkillsInput) {
        userSkillsInput.addEventListener("keydown", (e) => {
            if (e.key === "Enter") {
                e.preventDefault();
                findJobs();
            }
        });
    }

    const registerForm = document.getElementById("registerForm");
    const loginForm = document.getElementById("loginForm");
    const uploadButton = document.getElementById("uploadButton");
    const cameraButton = document.getElementById("cameraButton");
    const uploadPhotoButton = document.getElementById("uploadPhotoButton");
    const photoInput = document.getElementById("photoUpload");
    const captureButton = document.getElementById("capturePhotoButton");
    const resumeButton = document.getElementById("analyzeResumeButton");
    const downloadSampleButton = document.getElementById("downloadSampleResume");
    const expectedRoleSelect = document.getElementById("expectedJobRole");
    const jobDescription = document.getElementById("jobDescription");
    const resultPage = document.getElementById("resumeResultContent");
    const resultStatus = document.getElementById("resumeResultStatus");

    if (resultPage && resultStatus) {
        const savedResult = sessionStorage.getItem("resumeAnalysisResult") || localStorage.getItem("resume_result");
        if (savedResult) {
            try {
                displayJobMatches(JSON.parse(savedResult));
                resultPage.hidden = false;
                resultStatus.hidden = true;
            } catch (error) {
                console.error("Could not load saved resume analysis:", error);
                resultStatus.textContent = "The saved analysis could not be displayed. Please upload and analyze your resume again.";
            }
        } else {
            resultStatus.textContent = "No resume analysis is available in this tab. Upload a resume to view its results.";
        }
    }

    if (expectedRoleSelect && jobDescription) {
        loadJobRoles(expectedRoleSelect, jobDescription);
    }

    if (registerForm) {
        registerForm.addEventListener("submit", registerUser);
    }

    if (loginForm) {
        loginForm.addEventListener("submit", loginUser);
    }

    if (resumeButton) {
        resumeButton.addEventListener("click", uploadResume);
    }

    if (uploadButton) {
        uploadButton.addEventListener("click", uploadResume);
    }

    if (cameraButton) {
        cameraButton.addEventListener("click", startCamera);
    }

    if (uploadPhotoButton) {
        uploadPhotoButton.addEventListener("click", () => photoInput.click());
    }

    if (photoInput) {
        photoInput.addEventListener("change", handlePhotoUpload);
    }

    if (captureButton) {
        captureButton.addEventListener("click", capturePhoto);
    }

    if (downloadSampleButton) {
        downloadSampleButton.addEventListener("click", () =>
            downloadTailoredResume(downloadSampleButton)
        );
    }
});