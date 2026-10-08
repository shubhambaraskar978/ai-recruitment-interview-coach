import axios from "axios";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "/api",
  timeout: 120_000,
  withCredentials: true,
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    const detail = error.response?.data?.detail;
    const message =
      typeof detail === "string"
        ? detail
        : Array.isArray(detail)
          ? detail.map((issue) => issue.msg).filter(Boolean).join(" ")
          : "";
    const requestError = new Error(
      message
        ? message
        : error.code === "ECONNABORTED"
          ? "The request took too long. Please try again."
          : "The service is unavailable. Check that the backend is running and try again.",
    );
    requestError.status = error.response?.status;
    if (
      requestError.status === 401 &&
      !/\/auth\/(login|register|me|logout)$/.test(error.config?.url || "")
    ) {
      window.dispatchEvent(
        new CustomEvent("auth:expired", { detail: requestError.message }),
      );
    }
    return Promise.reject(requestError);
  },
);

export const resumeService = {
  analyze(file) {
    const form = new FormData();
    form.append("file", file);
    return api.post("/resume/analyze", form).then(({ data }) => data);
  },
};

export const jobMatchService = {
  analyze(resume_text, job_description) {
    return api
      .post("/job-match/analyze", { resume_text, job_description })
      .then(({ data }) => data);
  },
};

export const interviewService = {
  create(payload) {
    return api.post("/interviews", payload).then(({ data }) => data);
  },
  get(id) {
    return api.get(`/interviews/${id}`).then(({ data }) => data);
  },
  submitAnswer(id, answer) {
    return api
      .post(`/interviews/${id}/answer`, { answer })
      .then(({ data }) => data);
  },
  skip(id) {
    return api.post(`/interviews/${id}/skip`).then(({ data }) => data);
  },
  next(id) {
    return api.post(`/interviews/${id}/next`).then(({ data }) => data);
  },
  complete(id) {
    return api.post(`/interviews/${id}/complete`).then(({ data }) => data);
  },
  report(id) {
    return api.get(`/interviews/${id}/report`).then(({ data }) => data);
  },
};

export const healthService = {
  check() {
    return api.get("/health").then(({ data }) => data);
  },
};

export const authService = {
  register(payload) {
    return api.post("/auth/register", payload).then(({ data }) => data);
  },
  login(payload) {
    return api.post("/auth/login", payload).then(({ data }) => data);
  },
  me() {
    return api.get("/auth/me").then(({ data }) => data);
  },
  logout() {
    return api.post("/auth/logout").then(({ data }) => data);
  },
};

export const accountService = {
  dashboard() {
    return api.get("/account/dashboard").then(({ data }) => data);
  },
};

export default api;
