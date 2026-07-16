import { createApp } from "vue";

import { createWaitlistApi, WaitlistModule } from "./modules/waitlist";


const baseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";
const api = createWaitlistApi(baseUrl);

createApp(WaitlistModule, {
  api,
  courseId: "AI201",
}).mount("#app");
