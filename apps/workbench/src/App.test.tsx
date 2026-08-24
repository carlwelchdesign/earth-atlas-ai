import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { App } from "./App";

describe("App", () => {
  it("identifies the repository foundation without claiming operational capability", () => {
    render(<App />);

    expect(
      screen.getByRole("heading", { level: 1, name: "EchoAtlas" }),
    ).toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent(
      "operational capabilities have not been implemented",
    );
    expect(screen.getByText("No source imagery is loaded")).toBeInTheDocument();
  });
});
