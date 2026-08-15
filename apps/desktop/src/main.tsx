import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import App from "./App";
import PatronDesk from "./PatronDesk";
import "./styles.css";
import "./patron.css";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    <PatronDesk>
      <App />
    </PatronDesk>
  </StrictMode>,
);
