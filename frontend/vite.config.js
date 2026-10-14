import { fileURLToPath } from "node:url";
import { defineConfig } from "vite";

const htmlPage = (name) =>
    fileURLToPath(new URL(`./${name}`, import.meta.url));

export default defineConfig({
    base: "./",
    server: {
        proxy: {
            "/api": {
                target: "http://127.0.0.1:8000",
                changeOrigin: true,
            },
            "/health": {
                target: "http://127.0.0.1:8000",
                changeOrigin: true,
            },
        },
    },
    build: {
        rollupOptions: {
            input: {
                index: htmlPage("index.html"),
                login: htmlPage("login.html"),
                register: htmlPage("register.html"),
                dashboard: htmlPage("dashboard.html"),
                uploadResume: htmlPage("upload-resume.html"),
                uploadResumeLegacy: htmlPage("upload resume.html"),
                resumeResult: htmlPage("resume-result.html"),
                resumeResultLegacy: htmlPage("resume result.html"),
                jobMatching: htmlPage("job-matching.html"),
                jobMatchingLegacy: htmlPage("job matching .html"),
                dashboardWelcome: htmlPage("dash board wel.html"),
                darkAndLight: htmlPage("dark and light .html"),
            },
        },
    },
});
