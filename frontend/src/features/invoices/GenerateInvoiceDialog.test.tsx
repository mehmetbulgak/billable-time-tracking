import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { BillingPreview } from "@/shared/api/types";
import { buildClient, buildPreview } from "@/test/fixtures";
import { json, mockFetch, renderWithProviders, route } from "@/test/render";

import { GenerateInvoiceDialog } from "./GenerateInvoiceDialog";

const authenticated = { auth: { accessToken: "access", refreshToken: "refresh" } };

async function openWithPreview(preview: BillingPreview) {
  const { fetchMock, calls } = mockFetch(
    route("GET", "/api/v1/clients/", () =>
      json({ count: 1, next: null, previous: null, results: [buildClient()] }),
    ),
    route("GET", "/api/v1/invoices/preview/", () => json(preview)),
  );
  vi.stubGlobal("fetch", fetchMock);
  const user = userEvent.setup();
  renderWithProviders(<GenerateInvoiceDialog onClose={vi.fn()} />, {
    preloadedState: authenticated,
  });
  await user.click(screen.getByLabelText("Client"));
  await user.click(await screen.findByRole("option", { name: "Atlas Fintech" }));
  return { calls };
}

describe("GenerateInvoiceDialog", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("previews the lines before creating a draft", async () => {
    const { calls } = await openWithPreview(buildPreview());

    const table = await screen.findByRole("table");
    expect(within(table).getByText("Billable time")).toBeInTheDocument();
    expect(within(table).getAllByText("$1,437.50")).not.toHaveLength(0);
    expect(screen.getByRole("button", { name: "Create draft" })).toBeEnabled();
    const previewCall = calls.find((call) => call.url.includes("/invoices/preview/"));
    expect(new URL(previewCall?.url ?? "").searchParams.get("client")).toBe("5");
  });

  it("warns that an existing draft will be replaced", async () => {
    await openWithPreview(buildPreview({ replaces_draft: 42 }));

    expect(await screen.findByText(/already exists/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Replace draft" })).toBeEnabled();
  });

  it("does not offer a draft when there is nothing to bill", async () => {
    await openWithPreview(buildPreview({ lines: [], subtotal: "0.00", is_empty: true }));

    expect(await screen.findByText(/no billable work for Atlas Fintech/)).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Create draft" })).toBeDisabled();
  });
});
