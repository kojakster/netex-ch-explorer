import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import { HttpDataSource } from "./api";
import "./styles.css";

const root = document.getElementById("root");
if (root === null) {
  throw new Error("#root fehlt in index.html");
}
createRoot(root).render(
  <StrictMode>
    <App dataSource={new HttpDataSource()} />
  </StrictMode>,
);
