import { AfterViewChecked, Component, ElementRef, EventEmitter, HostListener, Input, Output, ViewChild } from "@angular/core";

@Component({
  selector: "kh-confirm-dialog",
  template: `
    @if (open) {
      <div class="dialog-backdrop">
        <section #dialog class="dialog" role="dialog" aria-modal="true" [attr.aria-labelledby]="titleId" [attr.aria-describedby]="descriptionId">
          <h2 [id]="titleId">{{ title }}</h2>
          <p [id]="descriptionId">{{ description }}</p>
          <div class="actions">
            <button #cancelButton type="button" class="secondary" (click)="cancel.emit()">{{ cancelLabel }}</button>
            <button type="button" class="danger" (click)="confirm.emit()">{{ confirmLabel }}</button>
          </div>
        </section>
      </div>
    }
  `,
  styles: [`.dialog-backdrop { position: fixed; z-index: 10; inset: 0; display: grid; place-items: center; padding: var(--space-5); background: rgb(23 32 51 / 48%); } .dialog { width: min(100%, 30rem); padding: var(--space-5); border-radius: var(--radius-md); background: var(--color-surface); box-shadow: var(--shadow-card); } h2, p { margin: 0; } p { margin-top: var(--space-3); color: var(--color-muted); } .actions { display: flex; justify-content: flex-end; flex-wrap: wrap; gap: var(--space-2); margin-top: var(--space-5); } button { padding: .6rem .85rem; border: 0; border-radius: var(--radius-sm); font: inherit; font-weight: 650; cursor: pointer; } .secondary { background: var(--color-neutral-soft); color: var(--color-text); } .danger { background: var(--color-danger); color: #fff; }`],
})
export class ConfirmDialogComponent implements AfterViewChecked {
  @Input() open = false;
  @Input() title = "Confirmar ação";
  @Input() description = "Esta ação pode ser difícil de reverter.";
  @Input() cancelLabel = "Cancelar";
  @Input() confirmLabel = "Confirmar";
  @Output() readonly confirm = new EventEmitter<void>();
  @Output() readonly cancel = new EventEmitter<void>();
  @ViewChild("dialog") private readonly dialog?: ElementRef<HTMLElement>;
  @ViewChild("cancelButton") private readonly cancelButton?: ElementRef<HTMLButtonElement>;
  private focused = false;

  get titleId(): string { return "confirm-dialog-title"; }
  get descriptionId(): string { return "confirm-dialog-description"; }

  ngAfterViewChecked(): void {
    if (this.open && !this.focused) {
      this.cancelButton?.nativeElement.focus();
      this.focused = true;
    }
    if (!this.open) this.focused = false;
  }

  @HostListener("document:keydown", ["$event"])
  onKeydown(event: KeyboardEvent): void {
    if (!this.open) return;
    if (event.key === "Escape") { event.preventDefault(); this.cancel.emit(); return; }
    if (event.key !== "Tab") return;
    const focusable = this.dialog?.nativeElement.querySelectorAll<HTMLElement>("button:not([disabled]), [href], input:not([disabled])");
    if (!focusable || focusable.length === 0) return;
    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
    if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
  }
}
