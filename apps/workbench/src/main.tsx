import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { App } from "./App";
import "maplibre-gl/dist/maplibre-gl.css";
import "./index.css";

const root = document.getElementById("root");

if (root === null) {
  throw new Error("EchoAtlas root element was not found");
}

createRoot(root).render(
  <StrictMode>
    <App initialMode="explore" />
  </StrictMode>,
);
