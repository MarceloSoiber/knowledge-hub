import { ComponentFixture, TestBed } from "@angular/core/testing";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { ConfirmDialogComponent } from "./confirm-dialog.component";

describe("ConfirmDialogComponent", () => {
  let fixture: ComponentFixture<ConfirmDialogComponent>;

  beforeEach(() => {
    TestBed.configureTestingModule({});
    fixture = TestBed.createComponent(ConfirmDialogComponent);
    fixture.componentRef.setInput("open", true);
    fixture.detectChanges();
  });

  afterEach(() => TestBed.resetTestingModule());

  it("uses modal semantics and focuses cancel when opened", () => {
    const dialog = fixture.nativeElement.querySelector("[role=dialog]") as HTMLElement;
    expect(dialog.getAttribute("aria-modal")).toBe("true");
    expect(document.activeElement?.textContent).toContain("Cancelar");
  });

  it("emits cancel on Escape and confirm only on the explicit action", () => {
    const component = fixture.componentInstance;
    const cancel = vi.fn();
    const confirm = vi.fn();
    component.cancel.subscribe(cancel);
    component.confirm.subscribe(confirm);

    document.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" }));
    expect(cancel).toHaveBeenCalledOnce();
    expect(confirm).not.toHaveBeenCalled();

    const buttons = fixture.nativeElement.querySelectorAll("button") as NodeListOf<HTMLButtonElement>;
    buttons[1].click();
    expect(confirm).toHaveBeenCalledOnce();
  });
});
