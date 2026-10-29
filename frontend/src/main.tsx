import "@fontsource-variable/inter";
import "dayjs/locale/en-gb";

import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { App } from "@/app/App";
import { makeStore } from "@/app/store";

const container = document.getElementById("root");

if (!container) {
  throw new Error("The #root element is missing from index.html.");
}

createRoot(container).render(
  <StrictMode>
    <App store={makeStore()} />
  </StrictMode>,
);
